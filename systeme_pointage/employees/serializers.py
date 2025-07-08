from rest_framework import serializers
from utils.face_recognition_utils import face_recognition_handler
from .models import Employee
from PIL import Image
import numpy as np
import logging

logger = logging.getLogger(__name__)

class SimpleEmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'immatricule', 'nom', 'prenom', 'email']

class EmployeeSerializer(serializers.ModelSerializer):
    departement_info = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id', 'immatricule', 'nom', 'prenom', 'adresse', 'email', 'telephone',
            'poste', 'departement', 'departement_info', 'photo_url', 'face_encoding',
            'is_active_employee', 'date_embauche', 'created_at', 'updated_at'
        ]
        read_only_fields = ['face_encoding', 'created_at', 'updated_at']

    def get_departement_info(self, obj):
        # Import local pour éviter circular import
        from departments.serializers import SimpleDepartmentSerializer
        if obj.departement:
            return SimpleDepartmentSerializer(obj.departement).data
        return None

    def get_photo_url(self, obj):
        request = self.context.get('request')
        if obj.photo:
            url = obj.photo.url
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        return None

class EmployeeCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)
    photo_file = serializers.ImageField(write_only=True, required=False)
    role = serializers.ChoiceField(
        choices=[('admin', 'Admin'), ('manager', 'Manager'), ('rh', 'RH'), ('employee', 'Employee')],
        write_only=True,
        required=True
    )

    class Meta:
        model = Employee
        fields = [
            'immatricule', 'nom', 'prenom', 'adresse', 'email', 'telephone',
            'poste', 'departement', 'photo_file', 'is_active_employee',
            'password', 'password_confirm', 'role'
        ]

    def validate_email(self, value):
        return value.strip().lower()

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")

        email = data.get('email').strip().lower()

        if Employee.objects.filter(immatricule=data['immatricule']).exists():
            raise serializers.ValidationError({"immatricule": "Cet immatricule existe déjà."})

        # Ne pas vérifier l'email ici, car il sera vérifié côté Authentication

        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('password_confirm', None)
        photo_file = validated_data.pop('photo_file', None)
        role = validated_data.pop('role')

        email = validated_data.get('email').strip().lower()
        validated_data['email'] = email

        employee = Employee(**validated_data)
        employee.set_password(password)
        employee.username = employee.immatricule
        employee.save()

        if photo_file:
            employee.photo.save(photo_file.name, photo_file, save=True)
            try:
                pil_image = Image.open(photo_file).convert('RGB')
                image_np = np.array(pil_image)
            except Exception as e:
                logger.error(f"Erreur conversion image : {e}")
                image_np = None

            if image_np is not None:
                encoding = face_recognition_handler.extract_face_encoding(image_np)
                if encoding is not None:
                    employee.face_encoding = encoding.tolist()
                    employee.save(update_fields=['face_encoding'])
                else:
                    logger.warning("Aucun encodage facial extrait.")
            else:
                logger.warning("Image non convertible pour encodage.")

        # Ne pas créer Authentication ici : fait en vue

        return employee
