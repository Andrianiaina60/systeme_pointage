from rest_framework import generics, status, views
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.http import HttpResponse
import csv
from django.db.models import Q, Sum
from rest_framework.views import APIView

from .models import Leave
from .serializers import (
    LeaveSerializer, LeaveCreateSerializer, LeaveActionSerializer,
    EmployeeWithLeaveBalanceSerializer, EmployeeOwnLeaveBalanceSerializer
)
from authentication.permissions import IsRHUser, IsManagerUser
from employees.models import Employee


# 1. Liste des congés selon rôle
class LeaveListView(generics.ListAPIView):
    serializer_class = LeaveSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', None)

        if user.is_staff or role in ['admin', 'rh']:
            return Leave.objects.all().order_by('-created_at')
        elif role == 'manager':
            return Leave.objects.filter(employee__departement=user.employee.departement).order_by('-created_at')
        else:
            return Leave.objects.filter(employee=user.employee).order_by('-created_at')


# 2. Création d’une demande congé (employé connecté)
class LeaveCreateView(generics.CreateAPIView):
    serializer_class = LeaveCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user.employee)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        leave_instance = serializer.instance
        full_data = LeaveSerializer(leave_instance).data
        return Response(full_data, status=status.HTTP_201_CREATED)


# 3. Détail, modification, suppression congé (avec restrictions)
class LeaveDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LeaveSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_staff or getattr(user, 'role', None) == 'admin':
            return Leave.objects.all()

        if getattr(user, 'role', None) == 'manager':
            return Leave.objects.filter(employee__departement=user.employee.departement)

        if getattr(user, 'role', None) == 'rh':
            return Leave.objects.all()

        return Leave.objects.filter(employee=user.employee)

    def update(self, request, *args, **kwargs):
        leave = self.get_object()
        if leave.status_conge != 'en_attente':
            return Response({'detail': "Impossible de modifier une demande déjà traitée."}, status=status.HTTP_400_BAD_REQUEST)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        leave = self.get_object()
        if leave.status_conge != 'en_attente':
            return Response({'detail': "Impossible de supprimer une demande déjà traitée."}, status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)


# 4. Action RH : valider/rejeter toutes les demandes
class RHLeaveActionView(APIView):
    permission_classes = [IsAuthenticated, IsRHUser]

    def post(self, request, pk):
        try:
            leave = Leave.objects.get(pk=pk)
        except Leave.DoesNotExist:
            return Response({"detail": "Demande introuvable."}, status=404)

        if leave.status_conge != 'en_attente':
            return Response({"detail": "Cette demande a déjà été traitée."}, status=400)

        serializer = LeaveActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        commentaire = serializer.validated_data.get('commentaire', '')

        if action == 'approve':
            leave.status_conge = 'approuve'
        elif action == 'reject':
            leave.status_conge = 'rejete'
        else:
            return Response({"detail": "Action invalide."}, status=400)

        leave.commentaire_admin = commentaire
        leave.approuve_par = request.user.employee
        leave.date_approbation = timezone.now()
        leave.save()

        return Response({
            "message": f"Demande {action}ée avec succès par RH.",
            "status": leave.status_conge
        }, status=200)

# 5. Action Manager : valider/rejeter demandes de son département uniquement
class ManagerLeaveActionView(APIView):
    permission_classes = [IsAuthenticated, IsManagerUser]

    def post(self, request, pk):
        try:
            leave = Leave.objects.get(pk=pk)
        except Leave.DoesNotExist:
            return Response({"detail": "Demande non trouvée."}, status=404)

        # Le manager ne peut pas valider sa propre demande
        if leave.employee == request.user.employee:
            return Response({"detail": "Cette demande ne peut pas être traitée par le manager."}, status=400)

        # Manager ne traite que les demandes de son département
        if leave.employee.departement != request.user.employee.departement:
            return Response({"detail": "Vous ne pouvez traiter que les demandes de votre département."}, status=403)

        if leave.status_conge != 'en_attente':
            return Response({"detail": "Cette demande a déjà été traitée."}, status=400)

        action = request.data.get('action')
        if action == 'valider':
            leave.status = 'valide_manager'
        elif action == 'rejeter':
            leave.status = 'rejete'
        else:
            return Response({"detail": "Action invalide. Utilisez 'valider' ou 'rejeter'."}, status=400)

        leave.validated_by_manager = request.user.employee  # si tu veux enregistrer le validateur
        leave.save()
        return Response({"detail": f"Demande {action} avec succès."})


# 6. Admin : peut voir toutes les demandes, mais ne peut pas valider — pas d’action de validation admin


# 7. Statistiques congés (admin, rh, employé)
class LeaveStatsView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        qs = Leave.objects.all()

        if not (user.is_staff or getattr(user, 'role', None) == 'admin' or getattr(user, 'role', None) == 'rh'):
            # Employé : ses congés uniquement
            qs = qs.filter(employee=user.employee)
        # Manager peut voir congés de son département
        elif getattr(user, 'role', None) == 'manager':
            qs = qs.filter(employee__departement=user.employee.departement)

        data = {
            'total': qs.count(),
            'en_attente': qs.filter(status_conge='en_attente').count(),
            'approuve': qs.filter(status_conge='approuve').count(),
            'rejete': qs.filter(status_conge='rejete').count(),
            'annule': qs.filter(status_conge='annule').count(),
        }
        return Response(data)


# 8. Solde congés employé connecté
class EmployeeOwnLeaveBalanceView(generics.RetrieveAPIView):
    serializer_class = EmployeeOwnLeaveBalanceSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.employee


# 9. Liste des employés avec total congés approuvés (admin, rh)
class EmployeeLeaveBalanceView(generics.ListAPIView):
    serializer_class = EmployeeWithLeaveBalanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or getattr(user, 'role', None) in ['admin', 'rh']:
            return Employee.objects.all()
        return Employee.objects.filter(id=user.employee.id)


# 10. Solde congés global ou par employé (admin, rh, employé)
class LeaveBalanceView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        employee_id = request.query_params.get('employee_id')

        if user.is_staff or getattr(user, 'role', None) in ['admin', 'rh']:
            if employee_id:
                leaves = Leave.objects.filter(employee_id=employee_id, status_conge='approuve')
            else:
                leaves = Leave.objects.filter(status_conge='approuve')
        elif getattr(user, 'role', None) == 'manager':
            leaves = Leave.objects.filter(employee__departement=user.employee.departement, status_conge='approuve')
        else:
            leaves = Leave.objects.filter(employee=user.employee, status_conge='approuve')

        total_days = leaves.aggregate(total=Sum('duree_jours'))['total'] or 0
        return Response({'total_conges_approuves': total_days})


# 11. Calendrier congés
class LeaveCalendarView(generics.ListAPIView):
    serializer_class = LeaveSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Leave.objects.all()
        if not (user.is_staff or getattr(user, 'role', None) in ['admin', 'rh']):
            if getattr(user, 'role', None) == 'manager':
                qs = qs.filter(employee__departement=user.employee.departement)
            else:
                qs = qs.filter(employee=user.employee)
        return qs.order_by('date_debut')

class LeaveTypeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        types = [{'key': key, 'label': label} for key, label in Leave.TYPE_CONGE_CHOICES]
        return Response(types)

class LeaveTypePublicView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        types = [{'key': key, 'label': label} for key, label in Leave.TYPE_CONGE_CHOICES]
        return Response(types)
    
# 12. Export CSV des congés (admin et rh)
class LeaveExportView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not (user.is_staff or getattr(user, 'role', None) in ['admin', 'rh']):
            return Response({'detail': 'Permission refusée.'}, status=status.HTTP_403_FORBIDDEN)

        leaves = Leave.objects.all().order_by('-created_at')
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="conges_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Employé', 'Type de congé', 'Motif', 'Date début', 'Date fin', 'Durée (jours)',
            'Statut', 'Commentaire Admin', 'Approuvé par', 'Date approbation', 'Créé le'
        ])

        for leave in leaves:
            writer.writerow([
                leave.id,
                str(leave.employee),
                leave.get_type_conge_display(),
                leave.motif,
                leave.date_debut.strftime('%Y-%m-%d') if leave.date_debut else '',
                leave.date_fin.strftime('%Y-%m-%d') if leave.date_fin else '',
                leave.duree_jours,
                leave.get_status_conge_display(),
                leave.commentaire_admin or '',
                str(leave.approuve_par) if leave.approuve_par else '',
                leave.date_approbation.strftime('%Y-%m-%d %H:%M:%S') if leave.date_approbation else '',
                leave.created_at.strftime('%Y-%m-%d %H:%M:%S') if leave.created_at else '',
            ])

        return response
