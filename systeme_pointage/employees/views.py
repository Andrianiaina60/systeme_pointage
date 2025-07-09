import logging
import traceback
from datetime import timedelta
from rest_framework import generics
from PIL import Image
import numpy as np

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction, IntegrityError

from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone
from rest_framework.exceptions import NotFound

from .models import Employee
from authentication.models import Authentication  
from authentication.permissions import IsAdminByRoleOrStaff

from .serializers import EmployeeSerializer, EmployeeCreateSerializer
from utils.face_recognition_utils import extract_face_encoding
# from employees.serializers import EmployeeWithLeaveBalanceSerializer
#from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import make_password
from departments.models import Department

logger = logging.getLogger(__name__)


class EmployeeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            auth_obj = Authentication.objects.get(id=user.id)
            role = auth_obj.role

            # Base queryset
            employees = Employee.objects.select_related('departement')

            # ✅ Accès en fonction du rôle
            if role in ['admin', 'rh']:
                # Admin et RH voient tous les employés
                pass
            elif role == 'manager':
                if hasattr(user, 'employee') and user.employee.departement:
                    employees = employees.filter(departement=user.employee.departement)
                else:
                    return Response({'error': 'Aucun département associé au manager.'}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({'error': 'Accès refusé. Rôle non autorisé.'}, status=status.HTTP_403_FORBIDDEN)

            # 🔍 Filtres facultatifs
            department_id = request.query_params.get('department')
            is_active = request.query_params.get('is_active')
            search = request.query_params.get('search')

            if department_id:
                employees = employees.filter(departement_id=department_id)
            if is_active is not None:
                employees = employees.filter(is_active_employee=is_active.lower() == 'true')
            if search:
                employees = employees.filter(
                    Q(nom__icontains=search) |
                    Q(prenom__icontains=search) |
                    Q(email__icontains=search) |
                    Q(immatricule__icontains=search)
                )

            employees = employees.order_by('nom', 'prenom')
            serializer = EmployeeSerializer(employees, many=True, context={'request': request})

            return Response({'employees': serializer.data, 'count': employees.count()}, status=status.HTTP_200_OK)

        except Authentication.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erreur récupération employés: {str(e)}")
            return Response({'error': 'Erreur interne.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
                
class EmployeeCreateView(APIView):
    from authentication.models import Authentication
    permission_classes = [IsAuthenticated, IsAdminByRoleOrStaff]

    def post(self, request):
        try:
            auth_obj = Authentication.objects.get(id=request.user.id)
            if auth_obj.role != 'admin':
                return Response({'error': 'Accès refusé. Administrateur requis.'}, status=status.HTTP_403_FORBIDDEN)

            serializer = EmployeeCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({'error': 'Données invalides', 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                employee = serializer.save()
                return Response({'message': 'Employé créé avec succès', 'employee': EmployeeSerializer(employee).data}, status=status.HTTP_201_CREATED)

        except Authentication.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erreur création employé: {str(e)}")
            return Response({'error': 'Erreur lors de la création de l\'employé'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# EmployeeDetailView pour utilisateurs lambda
class EmployeeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # Tout utilisateur authentifié peut voir un employé
        employee = get_object_or_404(Employee, pk=pk)
        serializer = EmployeeSerializer(employee)
        return Response({'employee': serializer.data}, status=status.HTTP_200_OK)

    def put(self, request, pk):
        try:
            auth_obj = Authentication.objects.get(id=request.user.id)
            employee = get_object_or_404(Employee, pk=pk)

            # L'utilisateur ne peut modifier que SON propre email et mot de passe
            if not hasattr(auth_obj, 'employee') or auth_obj.employee.id != employee.id:
                return Response({'error': "Accès refusé. Vous ne pouvez modifier que votre propre compte."}, status=status.HTTP_403_FORBIDDEN)

            updated = False

            # Email modifiable
            if 'email' in request.data:
                employee.email = request.data['email']
                try:
                    auth_emp = Authentication.objects.get(employee=employee)
                    auth_emp.email = request.data['email']
                    auth_emp.save()
                except Authentication.DoesNotExist:
                    pass
                updated = True

            # Mot de passe avec confirmation
            pwd = request.data.get('password')
            pwd_confirm = request.data.get('password_confirm')
            if pwd or pwd_confirm:
                if pwd != pwd_confirm:
                    return Response({'error': 'Les mots de passe ne correspondent pas'}, status=status.HTTP_400_BAD_REQUEST)
                hashed_password = make_password(pwd)
                try:
                    auth_emp = Authentication.objects.get(employee=employee)
                    auth_emp.password = hashed_password
                    auth_emp.save()
                except Authentication.DoesNotExist:
                    return Response({'error': "Compte d'authentification non trouvé"}, status=status.HTTP_404_NOT_FOUND)
                updated = True

            if updated:
                employee.save()
                return Response({'message': 'Informations modifiées avec succès', 'employee': EmployeeSerializer(employee).data}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Aucun champ modifiable fourni'}, status=status.HTTP_400_BAD_REQUEST)

        except Authentication.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erreur modification employé: {str(e)}")
            return Response({'error': 'Erreur lors de la modification'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        # Pas d'accès delete pour utilisateur lambda
        return Response({'error': 'Accès refusé'}, status=status.HTTP_403_FORBIDDEN)


class EmployeeToggleStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            auth_obj = Authentication.objects.get(id=request.user.id)
            if auth_obj.role != 'admin':
                return Response({'error': 'Accès refusé. Administrateur requis.'}, status=status.HTTP_403_FORBIDDEN)

            employee_id = request.data.get('employee_id')
            if not employee_id:
                return Response({'error': 'ID employé requis'}, status=status.HTTP_400_BAD_REQUEST)

            employee = get_object_or_404(Employee, id=employee_id)
            if hasattr(auth_obj, 'employee') and employee.id == auth_obj.employee.id:
                return Response({'error': 'Impossible de modifier votre propre statut'}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                employee.is_active_employee = not employee.is_active_employee
                employee.save()
                try:
                    auth_emp = Authentication.objects.get(employee=employee)
                    auth_emp.is_active = employee.is_active_employee
                    auth_emp.save()
                except Authentication.DoesNotExist:
                    pass

                action = "activé" if employee.is_active_employee else "désactivé"
                return Response({'message': f'Employé {action} avec succès', 'employee': EmployeeSerializer(employee).data}, status=status.HTTP_200_OK)

        except Authentication.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erreur changement statut employé: {str(e)}")
            return Response({'error': 'Erreur lors du changement de statut'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeeStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            auth_obj = Authentication.objects.get(id=request.user.id)
            if auth_obj.role != 'admin':
                return Response({'error': 'Accès refusé. Administrateur requis.'}, status=status.HTTP_403_FORBIDDEN)

            total_employees = Employee.objects.count()
            active_employees = Employee.objects.filter(is_active_employee=True).count()
            inactive_employees = total_employees - active_employees

            dept_stats = Employee.objects.values('departement__nom').annotate(
                count=Count('id'),
                active_count=Count('id', filter=Q(is_active_employee=True))
            ).order_by('departement__nom')

            thirty_days_ago = timezone.now() - timedelta(days=30)
            recent_employees = Employee.objects.filter(created_at__gte=thirty_days_ago).count()

            # Nouveauté : nombre d’employés en congé aujourd’hui
            today = date.today()
            from leaves.models import Leave  # adapter selon ton app

            en_conge_aujourdhui = Leave.objects.filter(
                statut='validé',
                date_debut__lte=today,
                date_fin__gte=today
            ).values('employee').distinct().count()

            # Nouveauté : solde total ou moyenne des congés (si champ solde_conge_annuel dans Employee)
            solde_total_conges = Employee.objects.aggregate(total_solde=Sum('solde_conge_annuel'))['total_solde']
            solde_moyen_conges = Employee.objects.aggregate(moyenne_solde=Avg('solde_conge_annuel'))['moyenne_solde']

            return Response({
                'stats': {
                    'total_employees': total_employees,
                    'active_employees': active_employees,
                    'inactive_employees': inactive_employees,
                    'recent_employees': recent_employees,
                    'en_conge_aujourdhui': en_conge_aujourdhui,
                    'solde_total_conges': solde_total_conges or 0,
                    'solde_moyen_conges': solde_moyen_conges or 0,
                    'departments': list(dept_stats)
                }
            }, status=status.HTTP_200_OK)

        except Authentication.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erreur statistiques employés: {str(e)}")
            return Response({'error': 'Erreur lors de la récupération des statistiques'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EmployeeSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response({"error": "Paramètre 'q' requis"}, status=status.HTTP_400_BAD_REQUEST)

        employees = Employee.objects.filter(
            Q(nom__icontains=query) |
            Q(prenom__icontains=query) |
            Q(email__icontains=query) |
            Q(immatricule__icontains=query)
        ).order_by('nom', 'prenom')

        serializer = EmployeeSerializer(employees, many=True)
        return Response({"results": serializer.data})


class EmployeesByDepartmentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, department_id):
        employees = Employee.objects.filter(departement_id=department_id).order_by('nom', 'prenom')
        serializer = EmployeeSerializer(employees, many=True)
        return Response({"employees": serializer.data})



class AdminCreateEmployeeView(APIView):
    permission_classes = [IsAuthenticated, IsAdminByRoleOrStaff]

    def post(self, request):
        serializer = EmployeeCreateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response({'error': 'Données invalides', 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data.get('email').strip().lower()
        immatricule = serializer.validated_data.get('immatricule')
        role = serializer.validated_data.get('role')
        password = serializer.validated_data.get('password')

        try:
            with transaction.atomic():
                # Verrouillage pour éviter les conflits
                Authentication.objects.select_for_update().filter(email=email).first()

                if Authentication.objects.filter(email=email).exists():
                    return Response({'error': 'Cet email est déjà utilisé.'}, status=status.HTTP_400_BAD_REQUEST)

                if Authentication.objects.filter(employee__immatricule=immatricule).exists():
                    return Response({'error': 'Un compte Authentication existe déjà pour cet immatricule.'}, status=status.HTTP_400_BAD_REQUEST)

                # Création de l'employé (sans créer l'Authentication dans le serializer)
                employee = serializer.save(is_active_employee=True)

                # Création du compte Authentication lié
                Authentication.objects.create(
                    employee=employee,
                    email=email,
                    role=role,
                    is_active=True,
                    is_staff=(role == 'admin'),
                    password=make_password(password)
                )

                employee_data = EmployeeSerializer(employee, context={'request': request}).data

                return Response({
                    'message': 'Employé créé avec succès',
                    'employee': employee_data,
                    'auth': {'email': email, 'role': role}
                }, status=status.HTTP_201_CREATED)

        except IntegrityError as e:
            logger.error(f"IntegrityError lors de la création employé: {e}")
            return Response({'error': 'Doublon détecté, email ou immatricule déjà utilisé.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur inconnue lors de la création employé: {e}")
            return Response({'error': 'Erreur lors de la création de l\'employé'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)      
        
class AdminListEmployeesView(EmployeeListView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            auth_obj = Authentication.objects.get(id=request.user.id)
            if auth_obj.role != 'admin':
                return Response({'error': 'Accès refusé. Administrateur requis.'}, status=status.HTTP_403_FORBIDDEN)

            employees = Employee.objects.all().order_by('nom', 'prenom')
            serializer = EmployeeSerializer(employees, many=True)
            
            total_employees = employees.count()  # compter le total
            
            return Response({
                'total': total_employees,
                'employees': serializer.data
            }, status=status.HTTP_200_OK)

        except Authentication.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erreur récupération employés (admin): {str(e)}")
            return Response({'error': 'Erreur lors de la récupération des employés'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
# AdminEmployeeDetailView réservé admin
class AdminEmployeeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, employee_id):
        try:
            return Employee.objects.get(pk=employee_id)
        except Employee.DoesNotExist:
            raise NotFound("Employé introuvable")

    def get(self, request, employee_id):
        if request.user.role != 'admin':
            return Response({'error': 'Accès refusé. Administrateur requis.'}, status=403)

        employee = self.get_object(employee_id)
        serializer = EmployeeSerializer(employee)
        return Response(serializer.data)

    def put(self, request, employee_id):
        if request.user.role != 'admin':
            return Response({'error': 'Accès refusé. Administrateur requis.'}, status=403)

        employee = self.get_object(employee_id)
        serializer = EmployeeSerializer(employee, data=request.data, partial=True)

        if serializer.is_valid():
            updated_employee = serializer.save()

            # ✅ Si le poste est "manager", définir ce manager dans le département
            poste = serializer.validated_data.get('poste')
            if poste == 'manager' and updated_employee.departement:
                departement = updated_employee.departement
                departement.manager = updated_employee
                departement.save()

            return Response(EmployeeSerializer(updated_employee).data)

        return Response(serializer.errors, status=400)

    def delete(self, request, employee_id):
        if request.user.role != 'admin':
            return Response({'error': 'Accès refusé. Administrateur requis.'}, status=403)

        employee = self.get_object(employee_id)
        with transaction.atomic():
            employee.is_active_employee = False  # désactivation logique
            employee.save()

            try:
                auth_emp = Authentication.objects.get(employee=employee)
                auth_emp.is_active = False
                auth_emp.save()
            except Authentication.DoesNotExist:
                pass

        return Response({'message': 'Employé désactivé avec succès'})

        
class AdminToggleEmployeeStatusView(EmployeeToggleStatusView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return EmployeeToggleStatusView.as_view()(request._request)


class AdminUpdateBiometricView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, employee_id):
        try:
            auth_obj = Authentication.objects.get(id=request.user.id)
            if auth_obj.role != 'admin':
                return Response({'error': 'Accès refusé. Administrateur requis.'}, status=status.HTTP_403_FORBIDDEN)

            employee = get_object_or_404(Employee, id=employee_id)
            image_file = request.FILES.get('image')
            if not image_file:
                return Response({'error': 'Image requise pour mise à jour biométrique'}, status=status.HTTP_400_BAD_REQUEST)

            encoding = extract_face_encoding(image_file)
            if not encoding:
                return Response({'error': "Visage non détecté dans l'image"}, status=status.HTTP_400_BAD_REQUEST)

            employee.face_encoding = encoding
            employee.save()

            return Response({'message': 'Données biométriques mises à jour avec succès', 'employee': EmployeeSerializer(employee).data}, status=status.HTTP_200_OK)

        except Authentication.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erreur mise à jour biométrique: {str(e)}")
            return Response({'error': 'Erreur lors de la mise à jour des données biométriques'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
