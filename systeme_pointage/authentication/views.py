import cv2
import numpy as np
import base64
import json
import logging
from django.contrib.auth.hashers import make_password
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction

# Models
from employees.models import Employee
from authentication.models import Authentication
from employees.serializers import EmployeeSerializer
from authentication.serializers import AuthenticationSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from employees.models import Employee
from authentication.serializers import UserSerializer  # Ton serializer pour l’utilisateur


# Importe ta fonction de reconnaissance faciale personnalisée, à adapter !
from utils.face_recognition_utils import recognize_face_from_image_file
from PIL import Image
import io



# Serializers
from authentication.serializers import (
    CustomTokenObtainPairSerializer,
    FacialLoginSerializer,
    ProfileSerializer,
    ProfileUpdateSerializer,
    LoginSerializer,
    EmployeeSerializer
)

# Utils
from utils.face_recognition_utils import (
    face_recognition_handler,
    compare_faces,
    load_biometric_data,
    extract_face_encoding,
    save_biometric_data,
    process_face_image
)

from authentication.permissions import IsAdminByRoleOrStaff

logger = logging.getLogger(__name__)


class LoginView(APIView):
    """
    Vue pour la connexion par email/password et reconnaissance faciale
    """
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            login_type = request.data.get('login_type', 'email')  # 'email' ou 'face'

            if login_type == 'email':
                return self._login_with_email(request)
            elif login_type == 'face':
                return self._login_with_face(request)
            else:
                return Response({'error': 'Type de connexion invalide'}, status=400)

        except Exception as e:
            logger.error(f"Erreur lors de la connexion: {str(e)}")
            return Response({'error': 'Erreur interne du serveur'}, status=500)

    def _login_with_email(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        email = serializer.validated_data['email'].lower()  # forcer lowercase
        password = serializer.validated_data['password']

        try:
            auth_obj = Authentication.objects.select_related('employee', 'employee__departement').get(email__iexact=email)

            if not auth_obj.check_password(password):
                return Response({'error': 'Email ou mot de passe incorrect'}, status=401)

            if not auth_obj.is_active:
                return Response({'error': 'Compte désactivé'}, status=401)

            if not auth_obj.employee.is_active_employee:
                return Response({'error': 'Compte employé désactivé'}, status=401)

            refresh = RefreshToken.for_user(auth_obj)

            return Response({
                'message': 'Connexion réussie',
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': {
                    'id': auth_obj.employee.id,
                    'immatricule': auth_obj.employee.immatricule,
                    'nom': auth_obj.employee.nom,
                    'email': auth_obj.email,
                    'role': auth_obj.role,
                    'poste': auth_obj.employee.poste,
                    'department': auth_obj.employee.departement.nom if auth_obj.employee.departement else None
                }
            }, status=200)

        except Authentication.DoesNotExist:
            return Response({'error': 'Email ou mot de passe incorrect'}, status=401)

    def _login_with_face(self, request):
        image_data = request.data.get('image')
        if not image_data:
            return Response({'error': 'Image requise pour la reconnaissance faciale'}, status=400)

        try:
            employee_id = face_recognition_handler.recognize_face(image_data)

            if employee_id:
                try:
                    employee = Employee.objects.get(id=employee_id)
                    auth_obj = Authentication.objects.get(employee=employee)

                    if not auth_obj.is_active:
                        return Response({'error': 'Compte désactivé'}, status=401)

                    if not employee.is_active_employee:
                        return Response({'error': 'Compte employé désactivé'}, status=401)

                    refresh = RefreshToken.for_user(auth_obj)

                    return Response({
                        'message': 'Connexion par reconnaissance faciale réussie',
                        'access_token': str(refresh.access_token),
                        'refresh_token': str(refresh),
                        'user': {
                            'id': employee.id,
                            'immatricule': employee.immatricule,
                            'nom': employee.nom,
                            'email': auth_obj.email,
                            'role': auth_obj.role,
                            'poste': employee.poste,
                            'department': employee.departement.nom if employee.departement else None
                        }
                    }, status=200)

                except (Employee.DoesNotExist, Authentication.DoesNotExist):
                    return Response({'error': 'Utilisateur non trouvé'}, status=404)
            else:
                return Response({'error': 'Visage non reconnu'}, status=401)

        except Exception as e:
            logger.error(f"Erreur lors de la reconnaissance faciale: {str(e)}")
            return Response({'error': 'Erreur lors du traitement de l\'image'}, status=500)


class FacialLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        image_file = request.FILES.get('photo_file')
        if not image_file:
            return Response({"error": "Photo file is required"}, status=400)

        try:
            image_bytes = image_file.read()
            pil_image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        except Exception:
            return Response({"error": "Format d'image non supporté"}, status=400)

        email = recognize_face_from_image_file(pil_image)
        if not email:
            return Response({"error": "Employé non reconnu"}, status=400)

        # Authentification classique via email (sans password ici)
        user = authenticate(request, email=email)
        if not user:
            return Response({"error": "Utilisateur non trouvé ou mot de passe requis"}, status=401)

        # Générer token JWT
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'email': user.email,
                'id': user.id,
                # autres champs utiles
            }
        })
        
class LogoutView(APIView):
    """
    Vue pour la déconnexion
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            return Response({'message': 'Déconnexion réussie'}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Erreur lors de la déconnexion: {str(e)}")
            return Response({'message': 'Déconnexion réussie'}, status=status.HTTP_200_OK)


class ProfileView(APIView):
    """
    Vue pour voir le profil utilisateur
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            auth_obj = Authentication.objects.select_related('employee', 'employee__departement').get(id=request.user.id)
            serializer = ProfileSerializer(auth_obj.employee)
            return Response({
                'profile': serializer.data,
                'email': auth_obj.email,
                'role': auth_obj.role
            }, status=status.HTTP_200_OK)
        except Authentication.DoesNotExist:
            return Response({'error': 'Profil introuvable'}, status=status.HTTP_404_NOT_FOUND)


class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            auth_obj = Authentication.objects.select_related('employee').get(id=request.user.id)

            # Ne garder que email et password en mise à jour
            auth_data = {}
            if 'email' in request.data:
                auth_data['email'] = request.data['email']

            if 'password' in request.data and request.data['password']:
                auth_obj.set_password(request.data['password'])

            with transaction.atomic():
                # Mettre à jour uniquement email dans Authentication
                if auth_data:
                    for key, value in auth_data.items():
                        setattr(auth_obj, key, value)
                    auth_obj.save()

                # Sauvegarder le password si modifié
                if 'password' in request.data and request.data['password']:
                    auth_obj.save()

            serializer = ProfileSerializer(auth_obj.employee)
            return Response({
                'message': 'Profil mis à jour avec succès',
                'profile': serializer.data,
                'email': auth_obj.email,
                'role': auth_obj.role
            }, status=status.HTTP_200_OK)

        except Authentication.DoesNotExist:
            return Response({'error': 'Profil introuvable'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du profil: {str(e)}")
            return Response({'error': 'Erreur lors de la mise à jour'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===== VUES ADMIN =====
class AdminEmployeeCreateView(APIView):
    """
    Vue pour créer un employé avec données biométriques (Admin seulement)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            auth_obj = Authentication.objects.get(id=request.user.id)
            if auth_obj.role != 'admin':
                return Response({'error': 'Accès non autorisé'}, status=status.HTTP_403_FORBIDDEN)
        except Authentication.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé'}, status=status.HTTP_404_NOT_FOUND)

        required_fields = ['immatricule', 'nom', 'poste', 'email', 'password']
        for field in required_fields:
            if not request.data.get(field):
                return Response({'error': f'Le champ {field} est requis'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Créer l'employé
                employee_data = {
                    'immatricule': request.data['immatricule'],
                    'nom': request.data['nom'],
                    'poste': request.data['poste'],
                    'departement_id': request.data.get('department_id'),
                    'is_active_employee': True,
                }
                employee = Employee.objects.create(**employee_data)

                # Enregistrement du visage si fourni
                face_image = request.data.get('face_image')
                if face_image:
                    success = face_recognition_handler.register_face(employee.id, face_image)
                    if not success:
                        raise ValueError("Impossible d'enregistrer le visage")

                # Créer l'objet d'authentification via le serializer (✅ CORRECTION ICI)
                auth_data = {
                    'employee': employee.id,
                    'email': request.data['email'],
                    'role': request.data.get('role', 'employee'),
                    'password': request.data['password']
                }

                auth_serializer = AuthenticationSerializer(data=auth_data)
                auth_serializer.is_valid(raise_exception=True)
                auth_serializer.save()  # Cela déclenche aussi _update_department_manager()

                return Response({
                    'message': 'Employé créé avec succès',
                    'employee': {
                        'id': employee.id,
                        'immatricule': employee.immatricule,
                        'nom': employee.nom,
                        'poste': employee.poste
                    }
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Erreur lors de la création de l'employé: {str(e)}")
            return Response({'error': f'Erreur lors de la création: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        
# class AdminEmployeeCreateView(APIView):
#     """
#     Vue pour créer un employé avec données biométriques (Admin seulement)
#     """
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         # Vérifier si l'utilisateur est admin
#         try:
#             auth_obj = Authentication.objects.get(id=request.user.id)
#             if auth_obj.role != 'admin':
#                 return Response({'error': 'Accès non autorisé'}, status=status.HTTP_403_FORBIDDEN)
#         except Authentication.DoesNotExist:
#             return Response({'error': 'Utilisateur non trouvé'}, status=status.HTTP_404_NOT_FOUND)

#         # Validation des données
#         required_fields = ['immatricule', 'nom', 'poste', 'email', 'password']
#         for field in required_fields:
#             if not request.data.get(field):
#                 return Response({'error': f'Le champ {field} est requis'}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             with transaction.atomic():
#                 # Créer l'employé
#                 employee_data = {
#                     'immatricule': request.data['immatricule'],
#                     'nom': request.data['nom'],
#                     'poste': request.data['poste'],
#                     'department_id': request.data.get('department_id'),
#                     'is_active_employee': True,
#                 }

#                 employee = Employee.objects.create(**employee_data)

#                 # Traiter les données biométriques si fournies
#                 face_image = request.data.get('face_image')
#                 if face_image:
#                     success = face_recognition_handler.register_face(employee.id, face_image)
#                     if not success:
#                         raise ValueError("Impossible d'enregistrer le visage")

#                 # Créer l'authentification avec mot de passe hashé
#                 auth_obj = Authentication(
#                     employee=employee,
#                     email=request.data['email'],
#                     role=request.data.get('role', 'employee')
#                 )
#                 auth_obj.set_password(request.data['password'])
#                 auth_obj.save()

#                 return Response({
#                     'message': 'Employé créé avec succès',
#                     'employee': {
#                         'id': employee.id,
#                         'immatricule': employee.immatricule,
#                         'nom': employee.nom,
#                         'poste': employee.poste
#                     }
#                 }, status=status.HTTP_201_CREATED)

#         except Exception as e:
#             logger.error(f"Erreur lors de la création de l'employé: {str(e)}")
#             return Response({'error': f'Erreur lors de la création: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


class AdminEmployeeListView(APIView):
    """
    Vue pour lister tous les employés (Admin seulement)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            auth_obj = Authentication.objects.get(id=request.user.id)
            if auth_obj.role != 'admin':
                return Response({'error': 'Accès non autorisé'}, status=status.HTTP_403_FORBIDDEN)
        except Authentication.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé'}, status=status.HTTP_404_NOT_FOUND)

        employees = Employee.objects.select_related('department').prefetch_related('authentication_set')
        serializer = EmployeeSerializer(employees, many=True)

        return Response({'employees': serializer.data}, status=status.HTTP_200_OK)


class AdminToggleEmployeeStatusView(APIView):
    """
    Vue pour activer/désactiver un employé (Admin seulement)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            auth_obj = Authentication.objects.get(id=request.user.id)
            if auth_obj.role != 'admin':
                return Response({'error': 'Accès non autorisé'}, status=status.HTTP_403_FORBIDDEN)
        except Authentication.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé'}, status=status.HTTP_404_NOT_FOUND)

        employee_id = request.data.get('employee_id')
        if not employee_id:
            return Response({'error': 'ID de l\'employé requis'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = Employee.objects.get(id=employee_id)
            employee.is_active = not employee.is_active
            employee.save()

            return Response({
                'message': f'Employé {"activé" if employee.is_active else "désactivé"} avec succès',
                'employee': EmployeeSerializer(employee).data
            }, status=status.HTTP_200_OK)

        except Employee.DoesNotExist:
            return Response({'error': 'Employé introuvable'}, status=status.HTTP_404_NOT_FOUND)


class AdminCreateEmployeeView(generics.CreateAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated, IsAdminByRoleOrStaff]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response({
            "message": "Employé créé avec succès",
            "employee": serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)
