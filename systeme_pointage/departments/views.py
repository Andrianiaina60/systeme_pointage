import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import Department
from .serializers import DepartmentSerializer, DepartmentCreateSerializer
from authentication.models import Authentication
from leaves.models import Leave  # si la gestion des congés est liée

logger = logging.getLogger(__name__)


class DepartmentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            departments = Department.objects.all().order_by('nom')
            serializer = DepartmentSerializer(departments, many=True)
            return Response({
                'departments': serializer.data,
                'count': departments.count()
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Erreur récupération des départements: {str(e)}")
            return Response({'error': 'Erreur lors de la récupération des départements'}, status=500)


class DepartmentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            auth_obj = Authentication.objects.get(id=request.user.id)
            if auth_obj.role != 'admin':
                return Response({'error': 'Accès non autorisé. Seuls les administrateurs peuvent créer des départements.'}, status=403)
        except Authentication.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé'}, status=404)

        serializer = DepartmentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': 'Données invalides', 'details': serializer.errors}, status=400)

        try:
            with transaction.atomic():
                department = serializer.save()
                return Response({'message': 'Département créé avec succès', 'department': DepartmentSerializer(department).data}, status=201)
        except Exception as e:
            logger.error(f"Erreur création département: {str(e)}")
            return Response({'error': 'Erreur création département'}, status=500)


class DepartmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            department = get_object_or_404(Department, pk=pk)
            serializer = DepartmentSerializer(department)
            return Response({'department': serializer.data}, status=200)
        except Exception as e:
            logger.error(f"Erreur récupération du département {pk}: {str(e)}")
            return Response({'error': 'Erreur récupération département'}, status=500)

    def put(self, request, pk):
        try:
            auth_obj = Authentication.objects.get(id=request.user.id)
            if auth_obj.role != 'admin':
                return Response({'error': 'Seuls les administrateurs peuvent modifier.'}, status=403)
        except Authentication.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé'}, status=404)

        try:
            department = get_object_or_404(Department, pk=pk)
            serializer = DepartmentCreateSerializer(department, data=request.data, partial=True)
            if not serializer.is_valid():
                return Response({'error': 'Données invalides', 'details': serializer.errors}, status=400)

            with transaction.atomic():
                updated_department = serializer.save()
                return Response({'message': 'Département mis à jour', 'department': DepartmentSerializer(updated_department).data}, status=200)
        except Exception as e:
            logger.error(f"Erreur update département {pk}: {str(e)}")
            return Response({'error': 'Erreur modification département'}, status=500)

    def delete(self, request, pk):
        try:
            auth_obj = Authentication.objects.get(id=request.user.id)
            if auth_obj.role != 'admin':
                return Response({'error': 'Seuls les administrateurs peuvent supprimer.'}, status=403)
        except Authentication.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé'}, status=404)

        try:
            department = get_object_or_404(Department, pk=pk)
            employee_count = department.employees.count()
            if employee_count > 0:
                return Response({'error': f'Impossible de supprimer. {employee_count} employé(s) assigné(s).'}, status=400)

            nom = department.nom
            department.delete()
            return Response({'message': f'Département \"{nom}\" supprimé.'}, status=200)
        except Exception as e:
            logger.error(f"Erreur suppression département {pk}: {str(e)}")
            return Response({'error': 'Erreur suppression département'}, status=500)


class DepartmentStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            logger.info(f"Demande de stats pour département id={pk}")
            department = get_object_or_404(Department, pk=pk)

            total_employees = department.employees.count()
            active_employees = department.employees.filter(is_active_employee=True).count()
            inactive_employees = total_employees - active_employees

            current_leaves = Leave.objects.filter(
                employee__department=department,
                status_conge='approuve'
            ).count()

            stats = {
                'department_info': DepartmentSerializer(department).data,
                'employee_stats': {
                    'total_employees': total_employees,
                    'active_employees': active_employees,
                    'inactive_employees': inactive_employees
                },
                'leave_stats': {
                    'current_leaves': current_leaves
                }
            }

            return Response({'stats': stats}, status=status.HTTP_200_OK)

        except Department.DoesNotExist:
            logger.warning(f"Département id={pk} non trouvé")
            return Response({'error': 'Département non trouvé'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Erreur stats département {pk}: {str(e)}")
            return Response({'error': 'Erreur lors de la récupération des statistiques'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
