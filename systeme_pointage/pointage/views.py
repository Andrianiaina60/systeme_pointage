# pointage/views.py
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, time
from .models import Pointage
from .serializers import PointageSerializer
from employees.models import Employee

class FacialCheckInView(generics.CreateAPIView):
    serializer_class = PointageSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
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
            return Response({'detail': 'Déjà pointé.'}, status=400)

        heure_limite = time(8, 0)
        if heure_entree > heure_limite:
            pointage.status = 'retard'
            pointage.retard = datetime.combine(today, heure_entree) - datetime.combine(today, heure_limite)
        else:
            pointage.status = 'present'
        pointage.save()
        return Response({'detail': 'Entrée enregistrée', 'status': pointage.status})

class FacialCheckOutView(generics.UpdateAPIView):
    serializer_class = PointageSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        employee = request.user.employee
        now = timezone.now()
        today = now.date()
        try:
            pointage = Pointage.objects.get(employee=employee, date=today)
        except Pointage.DoesNotExist:
            return Response({'detail': 'Aucun pointage d\'entrée trouvé.'}, status=404)

        if pointage.heure_sortie:
            return Response({'detail': 'Sortie déjà enregistrée.'}, status=400)

        pointage.heure_sortie = now.time()
        pointage.methode_sortie = 'facial'
        pointage.calculer_temps_travaille()
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

class AdminPointageStatsView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total = Pointage.objects.count()
        today = timezone.now().date()
        today_count = Pointage.objects.filter(date=today).count()
        retards = Pointage.objects.filter(status='retard').count()
        absents = Employee.objects.filter(is_active=True).exclude(id__in=Pointage.objects.filter(date=today).values_list('employee_id', flat=True)).count()
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

class AdminPointageNotificationsView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        all_employees = Employee.objects.filter(is_active=True)
        pointages_today = Pointage.objects.filter(date=today)
        present_ids = pointages_today.values_list('employee_id', flat=True)

        # Enlève la partie .exclude(status='conge') qui cause l'erreur car ce champ n'existe pas
        absents = all_employees.exclude(id__in=present_ids)

        retards = pointages_today.filter(status='retard')

        return Response({
            'date': today,
            'absents': [{'id': e.id, 'nom': e.nom} for e in absents],
            'retards': [{'id': p.employee.id, 'nom': p.employee.nom, 'heure_entree': p.heure_entree} for p in retards]
        })

