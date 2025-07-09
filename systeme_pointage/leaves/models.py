
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from employees.models import Employee

class Leave(models.Model):
    # ✅ Définition des constantes pour les statuts
    STATUS_EN_ATTENTE = 'en_attente'
    STATUS_VALIDE_MANAGER = 'valide_manager'
    STATUS_EN_ATTENTE_RH = 'en_attente_rh'
    STATUS_VALIDE = 'valide'
    STATUS_REJETE = 'rejete'

    TYPE_CONGE_CHOICES = [
        ('annuel', 'Congé annuel'),
        ('maladie', 'Congé maladie'),
        ('maternite', 'Congé maternité'),
        ('paternite', 'Congé paternité'),
        ('sans_solde', 'Congé sans solde'),
        ('exceptionnel', 'Congé exceptionnel'),
    ]

    TYPE_JUSTIFICATIF_CHOICES = [
        ('certificat', 'Certificat médical'),
        ('carnet', 'Carnet de santé'),
    ]

    STATUS_CHOICES = [
        (STATUS_EN_ATTENTE, 'En attente'),
        (STATUS_VALIDE_MANAGER, 'Validé par le manager'),
        (STATUS_EN_ATTENTE_RH, 'En attente validation RH'),
        (STATUS_VALIDE, 'Validé par le RH'),
        (STATUS_REJETE, 'Rejeté'),
    ]

    status_conge = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_EN_ATTENTE
    )

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leaves')
    type_conge = models.CharField(max_length=20, choices=TYPE_CONGE_CHOICES)
    motif = models.TextField()
    date_debut = models.DateField()
    date_fin = models.DateField()
    duree_jours = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    document_justificatif = models.FileField(upload_to='leave_documents/', blank=True, null=True)
    type_justificatif = models.CharField(max_length=20, choices=TYPE_JUSTIFICATIF_CHOICES, null=True, blank=True)

    assurance_entreprise = models.BooleanField(default=False, verbose_name="Assurance entreprise")
    commentaire_admin = models.TextField(blank=True, null=True)

    # ✅ Références des validateurs
    validated_by_manager = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='validated_leaves_by_manager'
    )
    validated_by_rh = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='validated_leaves_by_rh'
    )
    rejected_by = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rejected_leaves'
    )

    date_approbation = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leave'
        verbose_name = 'Congé'
        verbose_name_plural = 'Congés'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.nom} - {self.type_conge} ({self.date_debut} - {self.date_fin})"

    def clean(self):
        if self.date_debut and self.date_fin and self.date_debut > self.date_fin:
            raise ValidationError("La date de début ne peut pas être postérieure à la date de fin.")

    def save(self, *args, **kwargs):
        # ✅ Calcul automatique de la durée
        if self.date_debut and self.date_fin:
            self.duree_jours = (self.date_fin - self.date_debut).days + 1

        # ✅ Déduction du solde de congé si le congé est validé
        if self.pk:
            old = Leave.objects.filter(pk=self.pk).first()
            if (
                old
                and old.status_conge != self.STATUS_VALIDE
                and self.status_conge == self.STATUS_VALIDE
                and self.type_conge == 'annuel'
            ):
                if self.employee.solde_conge_annuel >= self.duree_jours:
                    self.employee.solde_conge_annuel -= self.duree_jours
                    self.employee.save()
                else:
                    raise ValidationError("Solde de congé annuel insuffisant.")

        super().save(*args, **kwargs)

# from django.db import models
# from django.core.validators import MinValueValidator
# from django.core.exceptions import ValidationError
# from employees.models import Employee

# class Leave(models.Model):
#     TYPE_CONGE_CHOICES = [
#         ('annuel', 'Congé annuel'),
#         ('maladie', 'Congé maladie'),
#         ('maternite', 'Congé maternité'),
#         ('paternite', 'Congé paternité'),
#         ('sans_solde', 'Congé sans solde'),
#         ('exceptionnel', 'Congé exceptionnel'),
#     ]

#     TYPE_JUSTIFICATIF_CHOICES = [
#         ('certificat', 'Certificat médical'),
#         ('carnet', 'Carnet de santé'),
#     ]

# # Leave.STATUS_EN_ATTENTE = 'en_attente'
# # Leave.STATUS_VALIDE_MANAGER = 'valide_manager'
# # Leave.STATUS_EN_ATTENTE_RH = 'en_attente_rh'
# # Leave.STATUS_VALIDE = 'valide'
# # Leave.STATUS_REJETE = 'rejete'

#     STATUS_CHOICES = [
#         ('en_attente', 'En attente'),
#         ('valide_manager', 'Validé par le manager'),
#         ('en_attente_rh', 'En attente validation RH'),
#         ('valide', 'Validé par le RH'),
#         ('rejete', 'Rejeté'),
#     ]

#     status_conge = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default='en_attente'
#     )

#     employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leaves')
#     type_conge = models.CharField(max_length=20, choices=TYPE_CONGE_CHOICES)
#     motif = models.TextField()
#     date_debut = models.DateField()
#     date_fin = models.DateField()
#     duree_jours = models.PositiveIntegerField(validators=[MinValueValidator(1)])

#     document_justificatif = models.FileField(upload_to='leave_documents/', blank=True, null=True)
#     type_justificatif = models.CharField(max_length=20, choices=TYPE_JUSTIFICATIF_CHOICES, null=True, blank=True)

#     assurance_entreprise = models.BooleanField(default=False, verbose_name="Assurance entreprise")

#     commentaire_admin = models.TextField(blank=True, null=True)

#     # ✅ Qui a validé ou rejeté ?
#     validated_by_manager = models.ForeignKey(
#         Employee, on_delete=models.SET_NULL, null=True, blank=True,
#         related_name='validated_leaves_by_manager'
#     )
#     validated_by_rh = models.ForeignKey(
#         Employee, on_delete=models.SET_NULL, null=True, blank=True,
#         related_name='validated_leaves_by_rh'
#     )
#     rejected_by = models.ForeignKey(
#         Employee, on_delete=models.SET_NULL, null=True, blank=True,
#         related_name='rejected_leaves'
#     )

#     date_approbation = models.DateTimeField(blank=True, null=True)

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         db_table = 'leave'
#         verbose_name = 'Congé'
#         verbose_name_plural = 'Congés'
#         ordering = ['-created_at']

#     def __str__(self):
#         return f"{self.employee.nom} - {self.type_conge} ({self.date_debut} - {self.date_fin})"

#     def clean(self):
#         if self.date_debut and self.date_fin and self.date_debut > self.date_fin:
#             raise ValidationError("La date de début ne peut pas être postérieure à la date de fin.")

#     def save(self, *args, **kwargs):
#         # calcul automatique de la durée
#         if self.date_debut and self.date_fin:
#             self.duree_jours = (self.date_fin - self.date_debut).days + 1

#         # soustraction du solde si le congé est validé définitivement
#         if self.pk:
#             old = Leave.objects.filter(pk=self.pk).first()
#             if (
#                 old
#                 and old.status_conge != 'valide'
#                 and self.status_conge == 'valide'
#                 and self.type_conge == 'annuel'
#             ):
#                 if self.employee.solde_conge_annuel >= self.duree_jours:
#                     self.employee.solde_conge_annuel -= self.duree_jours
#                     self.employee.save()
#                 else:
#                     raise ValidationError("Solde de congé annuel insuffisant.")

#         super().save(*args, **kwargs)



