from rest_framework import serializers
from .models import Leave
from employees.models import Employee
from django.db.models import Sum

# Serializer du département pour afficher ses détails dans l’employé
class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee._meta.get_field('departement').related_model  # Récupère le modèle Department lié
        fields = ['id', 'nom', 'description']

# 1. Serializer principal pour l'affichage des congés
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


# 2. Serializer pour la création de congés avec validation
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
        date_debut = attrs.get('date_debut')
        date_fin = attrs.get('date_fin')
        if date_debut and date_fin and date_debut > date_fin:
            raise serializers.ValidationError("La date de début ne peut pas être postérieure à la date de fin.")

        employee = self.context['request'].user.employee

        overlapping = Leave.objects.filter(
            employee=employee,
            status_conge__in=['en_attente', 'approuve'],
            date_debut__lte=date_fin,
            date_fin__gte=date_debut
        )
        if overlapping.exists():
            raise serializers.ValidationError("Vous avez déjà une demande de congé sur cette période.")

        duree = (date_fin - date_debut).days + 1
        type_conge = attrs.get('type_conge')

        limites = {
            'maternite': 98,
            'paternite': 3,
            'exceptionnel': 3,
            'maladie': 30,
            'annuel': getattr(employee, 'solde_conge_annuel', 0),
            'sans_solde': None
        }

        max_duree = limites.get(type_conge)
        if max_duree is not None and duree > max_duree:
            raise serializers.ValidationError(
                f"La durée demandée ({duree} jours) dépasse la limite autorisée pour un congé {type_conge} ({max_duree} jours max)."
            )

        # Justificatif requis pour congé maladie
        if type_conge == 'maladie':
            if not attrs.get('document_justificatif'):
                raise serializers.ValidationError("Un justificatif médical est obligatoire pour un congé maladie.")

            if not attrs.get('type_justificatif'):
                raise serializers.ValidationError("Veuillez préciser le type de justificatif : certificat ou carnet de santé.")

            if attrs.get('type_justificatif') not in ['certificat', 'carnet']:
                raise serializers.ValidationError("Le type de justificatif doit être 'certificat' ou 'carnet'.")

        return attrs


# 3. Serializer pour approuver / rejeter une demande de congé
class LeaveActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    commentaire = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs['action'] == 'reject' and not attrs.get('commentaire'):
            raise serializers.ValidationError("Un commentaire est requis pour rejeter une demande.")
        return attrs


# 4. Serializer pour lister les employés avec total congés approuvés
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


# 5. Serializer pour afficher le solde personnel de congés de l'employé connecté
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
