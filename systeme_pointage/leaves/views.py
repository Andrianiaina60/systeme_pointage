from rest_framework import generics, status, views
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.http import HttpResponse
import csv
from django.db.models import Q, Count, Sum

from .models import Leave
from .serializers import (
    LeaveSerializer, LeaveCreateSerializer, LeaveActionSerializer,
    EmployeeWithLeaveBalanceSerializer, EmployeeOwnLeaveBalanceSerializer
)
from authentication.permissions import IsAdminByRoleOrStaff, IsRHUser, IsManagerUser
from employees.models import Employee

from authentication.permissions import IsRHUser, IsManagerUser, IsAdminByRoleOrStaff
from rest_framework.views import APIView


# Manager : peut approuver/rejeter demandes de son département seulement
class ManagerLeaveActionView(APIView):
    permission_classes = [IsAuthenticated, IsManagerUser]

    def post(self, request, pk):
        try:
            leave = Leave.objects.get(pk=pk)
        except Leave.DoesNotExist:
            return Response({'detail': 'Demande introuvable'}, status=404)

        user_employee = getattr(request.user, 'employee', None)
        if not user_employee:
            return Response({'detail': "Utilisateur sans employé lié"}, status=400)

        # Vérifier que la demande est en attente manager
        if leave.status_conge != 'en_attente_manager':
            return Response({'detail': "Cette demande ne peut pas être traitée par le manager."}, status=400)

        if leave.employee.departement != user_employee.departement:
            return Response({'detail': "Permission refusée : demande hors département."}, status=403)

        serializer = LeaveActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        commentaire = serializer.validated_data.get('commentaire', '')

        if action == 'approve':
            leave.status_conge = 'en_attente_rh'  # passe à RH pour validation finale
        elif action == 'reject':
            leave.status_conge = 'rejete'  # rejet définitif côté manager
        else:
            return Response({'detail': "Action invalide."}, status=400)

        leave.commentaire_admin = commentaire
        leave.approuve_par = user_employee
        leave.date_approbation = timezone.now()
        leave.save()

        return Response({
            'message': f'Demande {action}ée par Manager',
            'status': leave.status_conge
        })


class RHLeaveActionView(APIView):
    permission_classes = [IsAuthenticated, IsRHUser]

    def post(self, request, pk):
        try:
            leave = Leave.objects.get(pk=pk)
        except Leave.DoesNotExist:
            return Response({'detail': 'Demande introuvable'}, status=404)

        # Vérifie que la demande est en attente RH
        if leave.status_conge != 'en_attente_rh':
            return Response({'detail': "Cette demande ne peut pas être traitée par le RH."}, status=400)

        serializer = LeaveActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        commentaire = serializer.validated_data.get('commentaire', '')

        if action == 'approve':
            leave.status_conge = 'approuve'  # validation finale
        elif action == 'reject':
            leave.status_conge = 'rejete'  # rejet final
        else:
            return Response({'detail': "Action invalide."}, status=400)

        leave.commentaire_admin = commentaire
        leave.approuve_par = getattr(request.user, 'employee', None)
        leave.date_approbation = timezone.now()
        leave.save()

        return Response({
            'message': f'Demande {action}ée par RH',
            'status': leave.status_conge
        })


        
# 1. Solde congés employé connecté
class EmployeeOwnLeaveBalanceView(generics.RetrieveAPIView):
    serializer_class = EmployeeOwnLeaveBalanceSerializer # ❌ mauvais serializer ici
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.employee


# 2. CRUD congés - création pour employé simple
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

# 3. Liste des congés selon rôle
class LeaveListView(generics.ListAPIView):
    serializer_class = LeaveSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Leave.objects.all()

        if user.is_staff or getattr(user, 'role', None) == 'admin':
            return qs.order_by('-created_at')

        if getattr(user, 'role', None) == 'manager':
            return qs.filter(employee__departement=user.employee.departement).order_by('-created_at')

        if getattr(user, 'role', None) == 'rh':
            return qs.filter(status_conge='approuve').order_by('-created_at')

        return qs.filter(employee=user.employee).order_by('-created_at')

# 4. Liste des types de congés (auth et public)
class LeaveTypeListView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        types = [{'key': key, 'label': label} for key, label in Leave.TYPE_CONGE_CHOICES]
        return Response(types)

class LeaveTypePublicView(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        types = [{'key': key, 'label': label} for key, label in Leave.TYPE_CONGE_CHOICES]
        return Response(types)

# 5. Détail, modification, suppression congé avec restrictions selon statut
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

# 6. Action individuelle Admin (approve / reject)
class LeaveActionView(views.APIView):
    permission_classes = [IsAuthenticated, IsAdminByRoleOrStaff]

    def post(self, request, pk):
        try:
            leave = Leave.objects.get(pk=pk)
            if leave.status_conge != 'en_attente':
                return Response({'detail': 'Cette demande a déjà été traitée.'}, status=status.HTTP_400_BAD_REQUEST)

            serializer = LeaveActionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            action = serializer.validated_data['action']
            commentaire = serializer.validated_data.get('commentaire', '')

            leave.status_conge = 'approuve' if action == 'approve' else 'rejete'
            leave.commentaire_admin = commentaire
            leave.approuve_par = request.user.employee
            leave.date_approbation = timezone.now()
            leave.save()

            return Response({
                'message': f'Demande de congé {action}ée avec succès',
                'leave_id': leave.id,
                'status': leave.status_conge
            }, status=status.HTTP_200_OK)

        except Leave.DoesNotExist:
            return Response({'detail': 'Demande de congé introuvable'}, status=status.HTTP_404_NOT_FOUND)

# 7. Action RH (approve/reject avec commentaire RH)
class RHLeaveActionView(views.APIView):
    permission_classes = [IsAuthenticated, IsRHUser]

    def post(self, request, pk):
        try:
            leave = Leave.objects.get(pk=pk)
            # Optionnel: vérifier que manager a approuvé
            if leave.status_conge != 'approuve':
                return Response({'detail': "Seules les demandes approuvées par le manager peuvent être traitées par RH."}, status=status.HTTP_400_BAD_REQUEST)

            serializer = LeaveActionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            action = serializer.validated_data['action']
            commentaire = serializer.validated_data.get('commentaire', '')

            leave.status_conge = 'approuve' if action == 'approve' else 'rejete'
            leave.commentaire_admin = commentaire
            leave.approuve_par = request.user.employee
            leave.date_approbation = timezone.now()
            leave.save()

            return Response({'message': f'Demande {action}ée par RH avec succès', 'status': leave.status_conge})

        except Leave.DoesNotExist:
            return Response({'detail': 'Demande introuvable'}, status=status.HTTP_404_NOT_FOUND)

# 8. Action Manager (valide ou refuse demande dans son département)
class ManagerLeaveActionView(views.APIView):
    permission_classes = [IsAuthenticated, IsManagerUser]

    def post(self, request, pk):
        try:
            leave = Leave.objects.get(pk=pk)
            if leave.employee.departement != request.user.employee.departement:
                return Response({'detail': "Permission refusée."}, status=status.HTTP_403_FORBIDDEN)

            if leave.status_conge != 'en_attente':
                return Response({'detail': "Cette demande a déjà été traitée."}, status=status.HTTP_400_BAD_REQUEST)

            serializer = LeaveActionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            action = serializer.validated_data['action']
            commentaire = serializer.validated_data.get('commentaire', '')

            leave.status_conge = 'approuve' if action == 'approve' else 'rejete'
            leave.commentaire_admin = commentaire
            leave.approuve_par = request.user.employee
            leave.date_approbation = timezone.now()
            leave.save()

            return Response({'message': f'Demande {action}ée par Manager avec succès', 'status': leave.status_conge})

        except Leave.DoesNotExist:
            return Response({'detail': 'Demande introuvable'}, status=status.HTTP_404_NOT_FOUND)

# 9. Statistiques congés (admin ou employé)
class LeaveStatsView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        qs = Leave.objects.all()

        if not (user.is_staff or getattr(user, 'role', None) == 'admin'):
            qs = qs.filter(employee=user.employee)

        data = {
            'total': qs.count(),
            'en_attente': qs.filter(status_conge='en_attente').count(),
            'approuve': qs.filter(status_conge='approuve').count(),
            'rejete': qs.filter(status_conge='rejete').count(),
            'annule': qs.filter(status_conge='annule').count(),
        }
        return Response(data)

# 10. Validation en masse par admin (approve/reject)
class LeaveApprovalView(views.APIView):
    permission_classes = [IsAuthenticated, IsAdminByRoleOrStaff]

    def post(self, request):
        leave_ids = request.data.get('leave_ids')
        action = request.data.get('action')
        commentaire = request.data.get('commentaire', '')

        if not leave_ids or not isinstance(leave_ids, list):
            return Response({'detail': 'leave_ids doit être une liste d\'IDs'}, status=status.HTTP_400_BAD_REQUEST)

        if action not in ['approve', 'reject']:
            return Response({'detail': 'Action invalide'}, status=status.HTTP_400_BAD_REQUEST)

        leaves = Leave.objects.filter(id__in=leave_ids, status_conge='en_attente')

        if not leaves.exists():
            return Response({'detail': 'Aucune demande valide à traiter'}, status=status.HTTP_404_NOT_FOUND)

        new_status = 'approuve' if action == 'approve' else 'rejete'

        updated_count = 0
        for leave in leaves:
            leave.status_conge = new_status
            leave.commentaire_admin = commentaire
            leave.approuve_par = request.user.employee
            leave.date_approbation = timezone.now()
            leave.save()
            updated_count += 1

        return Response({'detail': f'{updated_count} demandes {action}ées.'})

# 11. Visualiser solde congés annuel (admin, rh, employee)
class EmployeeLeaveBalanceView(generics.ListAPIView):
    serializer_class = EmployeeWithLeaveBalanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if user.is_staff or (hasattr(user, 'role') and user.role in ['admin', 'rh']):
            return Employee.objects.all()
        return Employee.objects.filter(id=user.employee.id)

# 12. Solde congés global ou par employé (admin ou employé)
class LeaveBalanceView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        employee_id = request.query_params.get('employee_id')

        if user.is_staff or getattr(user, 'role', None) == 'admin':
            if employee_id:
                leaves = Leave.objects.filter(employee_id=employee_id, status_conge='approuve')
            else:
                leaves = Leave.objects.filter(status_conge='approuve')
        else:
            leaves = Leave.objects.filter(employee=user.employee, status_conge='approuve')

        total_days = leaves.aggregate(total=Sum('duree_jours'))['total'] or 0
        return Response({'total_conges_approuves': total_days})

# 13. Calendrier congés
class LeaveCalendarView(generics.ListAPIView):
    serializer_class = LeaveSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Leave.objects.all()
        if not (user.is_staff or getattr(user, 'role', None) == 'admin'):
            qs = qs.filter(employee=user.employee)
        return qs.order_by('date_debut')

# 14. Export CSV des congés (admin)
class LeaveExportView(views.APIView):
    permission_classes = [IsAuthenticated, IsAdminByRoleOrStaff]

    def get(self, request):
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
