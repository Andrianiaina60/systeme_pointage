from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from employees.models import Employee
from authentication.models import Authentication

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personnalisé pour les tokens JWT
    """
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Ajouter des informations utilisateur au token
        try:
            auth_obj = Authentication.objects.select_related('employee').get(email=self.user.email)
            data['user'] = {
                'id': auth_obj.employee.id,
                'immatricule': auth_obj.employee.immatricule,
                'nom': auth_obj.employee.nom,
                'email': auth_obj.email,
                'role': auth_obj.role,
                'poste': auth_obj.employee.poste,
            }
        except Authentication.DoesNotExist:
            pass
        
        return data

class LoginSerializer(serializers.Serializer):
    """
    Serializer pour la connexion par email/password
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class FacialLoginSerializer(serializers.Serializer):
    """
    Serializer pour la connexion par reconnaissance faciale
    """
    image = serializers.CharField(help_text="Image en base64")

class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer pour le profil employé
    """
    departement_nom = serializers.CharField(source='departement.nom', read_only=True)
    
    class Meta:
        model = Employee
        fields = [
            'id', 'immatricule', 'nom', 'poste', 
            'departement', 'departement_nom', 'date_embauche', 
            'is_active'
        ]
        read_only_fields = ['id', 'immatricule', 'date_embauche']

class ProfileUpdateSerializer(serializers.Serializer):
    """
    Serializer pour la mise à jour du profil
    """
    nom = serializers.CharField(max_length=100, required=False)
    poste = serializers.CharField(max_length=100, required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(write_only=True, required=False)

class EmployeeSerializer(serializers.ModelSerializer):
    """
    Serializer pour les employés (vue admin)
    """
    departement_nom = serializers.CharField(source='departement.nom', read_only=True)
    email = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    
    class Meta:
        model = Employee
        fields = [
            'id', 'immatricule', 'nom', 'poste', 
            'departement', 'departement_nom', 'date_embauche', 
            'is_active', 'email', 'role'
        ]
    
    def get_email(self, obj):
        try:
            return obj.auth_user.email
        except:
            return None
    
    def get_role(self, obj):
        try:
            return obj.auth_user.role
        except:
            return None

# mis en jours de manager en manager de departement
class AuthenticationSerializer(serializers.ModelSerializer):
    employee = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.all())

    class Meta:
        model = Authentication
        fields = '__all__'

    def validate(self, data):
        role = data.get('role')
        employee = data.get('employee')

        if role == 'manager':
            if not employee:
                raise serializers.ValidationError("Un manager doit être lié à un employé.")
            if employee.poste != 'manager':
                raise serializers.ValidationError("L'employé doit avoir le poste 'manager' si rôle est manager.")
            if not employee.departement:
                raise serializers.ValidationError("Le manager doit être lié à un département.")

        return data

    def create(self, validated_data):
        auth = super().create(validated_data)
        self._update_department_manager(auth)
        return auth

    def update(self, instance, validated_data):
        auth = super().update(instance, validated_data)
        self._update_department_manager(auth)
        return auth

    def _update_department_manager(self, auth):
        if auth.role == 'manager' and auth.employee.departement:
            departement = auth.employee.departement
            if departement.manager_id != auth.employee.id:
                departement.manager = auth.employee
                departement.save()