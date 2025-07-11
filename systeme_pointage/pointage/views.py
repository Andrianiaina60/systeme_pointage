# pointage/views.py
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from datetime import datetime, timedelta, time, date
from django.db.models import Q
from .models import Pointage
from .serializers import PointageSerializer
from employees.models import Employee
from leaves.models import Leave
from authentication.permissions import IsRHOrAdmin  # custom permission
import logging
from datetime import date
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

class FacialCheckInView(APIView):
    serializer_class = PointageSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        employee = request.user.employee
        now = timezone.now()
        heure_entree = now.time()
        today = now.date()

        pointage, created = Pointage.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={'heure_entree': heure_entree, 'methode_entree': 'facial'}
        )

        if not created:
            return Response({'detail': 'Déjà pointé ,demain matin à 8h00 .'}, status=400)

        heure_limite = time(8, 0)
        if heure_entree > heure_limite:
            pointage.status = 'retard'
            pointage.retard = datetime.combine(today, heure_entree) - datetime.combine(today, heure_limite)
        else:
            pointage.status = 'present'
        pointage.save()
        return Response({'detail': 'Entrée enregistrée', 'status': pointage.status})

class FacialCheckOutView(APIView):
    serializer_class = PointageSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        employee = request.user.employee
        now = timezone.now()
        today = now.date()
        try:
            pointage = Pointage.objects.get(employee=employee, date=today)
        except Pointage.DoesNotExist:
            return Response({'detail': "Aucun pointage d'entrée trouvé."}, status=404)

        if pointage.heure_sortie:
            return Response({'detail': 'Sortie déjà enregistrée.'}, status=400)

        pointage.heure_sortie = now.time()
        pointage.methode_sortie = 'facial'
        pointage.calculer_temps_travaille()
        pointage.save()
        return Response({'detail': 'Sortie enregistrée', 'temps_travaille': pointage.temps_travaille})

class PointageListView(generics.ListAPIView):
    serializer_class = PointageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Pointage.objects.filter(employee=self.request.user.employee)

class PointageTodayView(generics.RetrieveAPIView):
    serializer_class = PointageSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return Pointage.objects.filter(employee=self.request.user.employee, date=timezone.now().date()).first()

class AdminPointageListView(generics.ListAPIView):
    serializer_class = PointageSerializer
    queryset = Pointage.objects.all()
    permission_classes = [IsAuthenticated]

class AdminPointageStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        total = Pointage.objects.count()
        today_count = Pointage.objects.filter(date=today).count()
        retards = Pointage.objects.filter(status='retard').count()
        absents = Employee.objects.filter(is_active=True).exclude(
            id__in=Pointage.objects.filter(date=today).values_list('employee_id', flat=True)
        ).count()
        return Response({
            'total_pointages': total,
            'aujourdhui': today_count,
            'retards': retards,
            'absents': absents
        })

class AdminPointageReportsView(generics.ListAPIView):
    serializer_class = PointageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        start = self.request.query_params.get('start')
        end = self.request.query_params.get('end')
        queryset = Pointage.objects.all()
        if start and end:
            queryset = queryset.filter(date__range=[start, end])
        return queryset

class AdminEmployeeAttendanceView(generics.ListAPIView):
    serializer_class = PointageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        employee_id = self.kwargs['employee_id']
        return Pointage.objects.filter(employee_id=employee_id)

class AdminPointageNotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = date.today()  # ou timezone.now().date() si tu veux gérer les fuseaux horaires

        # Récupérer les employés en congé validé aujourd'hui
        conges_valide_ids = Leave.objects.filter(
            status_conge='valide',
            date_debut__lte=today,
            date_fin__gte=today,
            type_conge__in=['annuel', 'paternite', 'maternite', 'exceptionnel']
        ).values_list('employee_id', flat=True)

        # Employés actifs qui ont pointé aujourd'hui
        present_ids = Pointage.objects.filter(date=today).values_list('employee_id', flat=True)

        # Absents = employés actifs non présents ET pas en congé validé
        absents = Employee.objects.filter(is_active=True) \
            .exclude(id__in=present_ids) \
            .exclude(id__in=conges_valide_ids)

        # Retards = pointages avec status retard aujourd’hui
        retards = Pointage.objects.filter(date=today, status='retard')

        return Response({
            'date': today,
            'absents': [{'id': e.id, 'nom': e.nom} for e in absents],
            'retards': [{'id': p.employee.id, 'nom': p.employee.nom, 'heure_entree': p.heure_entree} for p in retards]
        })

class ManagerDepartmentPointagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            if not hasattr(user, 'employee'):
                return Response({'error': 'Aucun employé associé.'}, status=403)
            emp = user.employee
            if emp.poste != 'manager':
                return Response({'error': 'Accès réservé aux managers.'}, status=403)
            today = date.today()
            department = emp.departement
            on_leave = Leave.objects.filter(
                employee__departement=department,
                status_conge='valide',
                date_debut__lte=today,
                date_fin__gte=today,
                type_conge__in=['annuel', 'paternite', 'maternite', 'exceptionnel']
            ).values_list('employee_id', flat=True)
            employees = Employee.objects.filter(departement=department).exclude(id__in=on_leave)
            data = []
            for emp in employees:
                pointage = Pointage.objects.filter(employee=emp, date=today).first()
                checked_in = pointage.heure_entree if pointage else None
                checked_out = pointage.heure_sortie if pointage else None
                retard = None
                if checked_in and checked_in > time(8, 0):
                    retard = True
                elif not checked_in:
                    retard = True
                data.append({
                    'id': emp.id,
                    'nom': emp.nom,
                    'prenom': emp.prenom,
                    'checked_in': checked_in,
                    'checked_out': checked_out,
                    'retard': retard,
                })
            return Response({'pointages': data})
        except Exception as e:
            logger.error(f"Erreur vue pointages manager: {str(e)}")
            return Response({'error': 'Erreur interne'}, status=500)

class AdminOrRHPointageStatsView(APIView):
    permission_classes = [IsAuthenticated, IsRHOrAdmin]

    def get(self, request):
        try:
            today = date.today()
            reference_time = time(8, 0)
            periode = 7
            on_leave_ids = Leave.objects.filter(
                date_debut__lte=today,
                date_fin__gte=today,
                status_conge='valide',
                type_conge__in=['annuel', 'paternite', 'maternite', 'exceptionnel']
            ).values_list('employee_id', flat=True)
            employees = Employee.objects.exclude(id__in=on_leave_ids)
            result = []
            for emp in employees:
                pt_today = Pointage.objects.filter(employee=emp, date=today).first()
                heure_arrivee = pt_today.heure_entree if pt_today else None
                retard_today = False
                retard_today_str = None
                if not heure_arrivee:
                    retard_today = True
                    retard_today_str = "Absent"
                elif heure_arrivee > reference_time:
                    retard_today = True
                    delta = datetime.combine(today, heure_arrivee) - datetime.combine(today, reference_time)
                    retard_today_str = f"{delta.seconds // 3600:02d}:{(delta.seconds // 60) % 60:02d}"
                else:
                    retard_today_str = "00:00"
                start_date = today - timedelta(days=periode)
                pointages = Pointage.objects.filter(employee=emp, date__range=(start_date, today))
                total_retards = 0
                total_minutes = 0
                for pt in pointages:
                    if not pt.heure_entree or pt.heure_entree > reference_time:
                        total_retards += 1
                        if pt.heure_entree:
                            delta = datetime.combine(pt.date, pt.heure_entree) - datetime.combine(pt.date, reference_time)
                            total_minutes += delta.seconds // 60
                        else:
                            total_minutes += 60
                sanction = total_minutes >= 60
                result.append({
                    "id": emp.id,
                    "nom": emp.nom,
                    "prenom": emp.prenom,
                    "checked_in": str(heure_arrivee) if heure_arrivee else None,
                    "retard_aujourdhui": retard_today,
                    "heure_retard_aujourdhui": retard_today_str,
                    "total_retards": total_retards,
                    "cumul_retard_minutes": total_minutes,
                    "retard_a_compenser": f"{total_minutes // 60:02d}:{total_minutes % 60:02d}",
                    "sanction": sanction
                })
            return Response({"retards": result}, status=200)
        except Exception as e:
            logger.error(f"Erreur stats retards: {str(e)}")
            return Response({'error': 'Erreur interne.'}, status=500)

class ManagerDepartmentRetardsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if not hasattr(user, 'employee') or user.employee.poste != 'manager':
            return Response({'error': 'Accès réservé aux managers.'}, status=403)

        manager = user.employee
        department = manager.departement
        today = date.today()
        reference_time = time(8, 0)
        periode = 7

        # Exclure les employés en congé validé
        conges_ids = Leave.objects.filter(
            employee__departement=department,
            status_conge='valide',
            date_debut__lte=today,
            date_fin__gte=today,
            type_conge__in=['annuel', 'paternite', 'maternite', 'exceptionnel']
        ).values_list('employee_id', flat=True)

        employees = Employee.objects.filter(departement=department, is_active=True).exclude(id__in=conges_ids)

        result = []

        for emp in employees:
            pt_today = Pointage.objects.filter(employee=emp, date=today).first()
            heure_arrivee = pt_today.heure_entree if pt_today else None

            retard_today = False
            retard_today_str = "Absent"
            if heure_arrivee and heure_arrivee > reference_time:
                retard_today = True
                delta = datetime.combine(today, heure_arrivee) - datetime.combine(today, reference_time)
                retard_today_str = f"{delta.seconds // 3600:02d}:{(delta.seconds // 60) % 60:02d}"
            elif heure_arrivee:
                retard_today_str = "00:00"
            else:
                retard_today = True

            start_date = today - timedelta(days=periode)
            pointages = Pointage.objects.filter(employee=emp, date__range=(start_date, today))

            total_retards = 0
            total_minutes = 0
            for pt in pointages:
                if not pt.heure_entree or pt.heure_entree > reference_time:
                    total_retards += 1
                    if pt.heure_entree:
                        delta = datetime.combine(pt.date, pt.heure_entree) - datetime.combine(pt.date, reference_time)
                        total_minutes += delta.seconds // 60
                    else:
                        total_minutes += 60  # Absent = 1h

            sanction = total_minutes >= 60

            result.append({
                "id": emp.id,
                "nom": emp.nom,
                "prenom": emp.prenom,
                "checked_in": str(heure_arrivee) if heure_arrivee else None,
                "retard_aujourdhui": retard_today,
                "heure_retard_aujourdhui": retard_today_str,
                "total_retards": total_retards,
                "cumul_retard_minutes": total_minutes,
                "retard_a_compenser": f"{total_minutes // 60:02d}:{total_minutes % 60:02d}",
                "sanction": sanction
            })

        return Response({'retards': result})

class NotifyLateEmployeesView(APIView):
    permission_classes = [IsAuthenticated]  # ⚠️ À restreindre à admin ou RH en production

    def get(self, request):
        today = date.today()
        start_week = today - timedelta(days=today.weekday())  # Lundi
        end_week = today  # Jusqu’à aujourd’hui

        reference_time = time(8, 0)

        employees = Employee.objects.filter(is_active=True)

        count_sent = 0

        for emp in employees:
            if not emp.email:
                continue

            pointages = Pointage.objects.filter(employee=emp, date__range=[start_week, end_week])
            total_retards = 0
            total_minutes = 0

            for pt in pointages:
                if not pt.heure_entree or pt.heure_entree > reference_time:
                    total_retards += 1
                    if pt.heure_entree:
                        delta = datetime.combine(pt.date, pt.heure_entree) - datetime.combine(pt.date, reference_time)
                        total_minutes += delta.seconds // 60
                    else:
                        total_minutes += 60  # Absent = 60 min

            if total_minutes > 0:
                # ✅ Envoyer l'email
                subject = "Notification de retard - Semaine en cours"
                message = f"""
Bonjour {emp.nom} {emp.prenom},

Voici votre récapitulatif de retards pour la semaine en cours ({start_week} au {end_week}) :

- Nombre de jours en retard : {total_retards}
- Total cumulé de retard : {total_minutes} minutes

Merci de veiller à votre ponctualité.

Service RH
"""
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=None,
                    recipient_list=[emp.email],
                    fail_silently=True,
                )
                count_sent += 1

        return Response({'message': f'{count_sent} e-mails envoyés aux employés en retard.'})

