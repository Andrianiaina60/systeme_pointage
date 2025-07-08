from rest_framework import serializers
from .models import Leave
from employees.models import Employee
from django.db.models import Sum

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee._meta.get_field('departement').related_model
        fields = ['id', 'nom', 'description']

class LeaveSerializer(serializers.ModelSerializer):
    employee = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Leave
        fields = [
            'id', 'employee', 'type_conge', 'motif', 'date_debut', 'date_fin',
            'duree_jours', 'status_conge', 'document_justificatif',
            'commentaire_admin', 'approuve_par', 'date_approbation',
            'assurance_entreprise', 'type_justificatif', 'created_at'
        ]
        read_only_fields = [
            'employee', 'duree_jours', 'status_conge', 'commentaire_admin',
            'approuve_par', 'date_approbation', 'created_at'
        ]

class LeaveCreateSerializer(serializers.ModelSerializer):
    type_justificatif = serializers.ChoiceField(
        choices=[('certificat', 'Certificat médical'), ('carnet', 'Carnet de santé')],
        required=False, allow_null=True
    )

    class Meta:
        model = Leave
        fields = [
            'type_conge', 'motif', 'date_debut', 'date_fin',
            'document_justificatif', 'assurance_entreprise', 'type_justificatif'
        ]

    def validate(self, attrs):
        # ... même logique que dans ton code initial
        return attrs

class LeaveActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    commentaire = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs['action'] == 'reject' and not attrs.get('commentaire'):
            raise serializers.ValidationError("Un commentaire est requis pour rejeter une demande.")
        return attrs

class EmployeeWithLeaveBalanceSerializer(serializers.ModelSerializer):
    total_conges_approuves = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id', 'nom', 'prenom', 'email', 'poste', 'departement',
            'is_active_employee', 'total_conges_approuves'
        ]

    def get_total_conges_approuves(self, employee):
        return Leave.objects.filter(employee=employee, status_conge='approuve')\
                            .aggregate(total=Sum('duree_jours'))['total'] or 0

class EmployeeOwnLeaveBalanceSerializer(serializers.ModelSerializer):
    departement_info = DepartmentSerializer(source='departement', read_only=True)
    total_conges_approuves = serializers.SerializerMethodField()
    demandes_en_attente = serializers.SerializerMethodField()
    total_restant = serializers.SerializerMethodField()
    solde_conge_annuel = serializers.IntegerField(read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'nom', 'prenom', 'email', 'poste', 'departement', 'departement_info', 'is_active_employee',
            'solde_conge_annuel', 'total_conges_approuves', 'total_restant', 'demandes_en_attente'
        ]

    def get_total_conges_approuves(self, employee):
        return Leave.objects.filter(employee=employee, status_conge='approuve')\
                            .aggregate(total=Sum('duree_jours'))['total'] or 0

    def get_demandes_en_attente(self, employee):
        return Leave.objects.filter(employee=employee, status_conge='en_attente').count()

    def get_total_restant(self, employee):
        total = self.get_total_conges_approuves(employee)
        return max(employee.solde_conge_annuel - total, 0)
