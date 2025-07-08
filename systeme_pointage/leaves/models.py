from django.db import models
from django.core.validators import MinValueValidator
from employees.models import Employee
from django.core.exceptions import ValidationError

class Leave(models.Model):
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
    
    # STATUS_CHOICES = [
    #     ('en_attente_manager', 'En attente validation manager'),
    #     ('en_attente_rh', 'En attente validation RH'),
    #     ('approuve', 'Approuvé'),
    #     ('rejete', 'Rejeté'),
    #     ('annule', 'Annulé'),
    # ]

    STATUS_CHOICES = [
        ('en_attente', 'En attente'),
        ('approuve', 'Approuvé'),
        ('rejete', 'Rejeté'),
        ('annule', 'Annulé'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leaves')
    type_conge = models.CharField(max_length=20, choices=TYPE_CONGE_CHOICES)
    motif = models.TextField()
    date_debut = models.DateField()
    date_fin = models.DateField()
    duree_jours = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    status_conge = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_attente')

    document_justificatif = models.FileField(upload_to='leave_documents/', blank=True, null=True)
    type_justificatif = models.CharField(max_length=20, choices=TYPE_JUSTIFICATIF_CHOICES, null=True, blank=True)
    
    assurance_entreprise = models.BooleanField(default=False, verbose_name="Assurance entreprise")

    commentaire_admin = models.TextField(blank=True, null=True)
    approuve_par = models.ForeignKey(Employee, on_delete=models.SET_NULL, blank=True, null=True, related_name='approved_leaves')
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
        if self.date_debut and self.date_fin:
            self.duree_jours = (self.date_fin - self.date_debut).days + 1
        
        # Exemple de gestion du solde congé annuel (adapter selon besoin)
        if self.pk:
            old = Leave.objects.filter(pk=self.pk).first()
            if (
                old
                and old.status_conge != 'approuve'
                and self.status_conge == 'approuve'
                and self.type_conge == 'annuel'
            ):
                if self.employee.solde_conge_annuel >= self.duree_jours:
                    self.employee.solde_conge_annuel -= self.duree_jours
                    self.employee.save()
                else:
                    raise ValidationError("Solde de congé annuel insuffisant.")
        
        super().save(*args, **kwargs)





# ✅ annuel — Congé annuel

#     Définition : C’est le congé payé que chaque salarié cumule selon son contrat.

#     Utilisation : Vacances, repos personnel.

#     Durée typique : 2.5 jours ouvrés par mois travaillé (soit 30 jours par an).

# ✅ maternite — Congé maternité

#     Définition : Accordé à une femme salariée enceinte avant et après l’accouchement.

#     Utilisation : Grossesse et accouchement.

#     Durée légale à Madagascar : 14 semaines (98 jours), dont 8 semaines après l’accouchement.

# ✅ paternite — Congé paternité

#     Définition : Accordé au père salarié à la naissance de son enfant.

#     Utilisation : Présence à la naissance, soutien à la mère.

#     Durée : Selon la législation ou les conventions collectives (souvent 3 jours à Madagascar, sauf accord plus favorable).

# ✅ sans_solde — Congé sans solde

#     Définition : Congé pris sans être payé.

#     Utilisation : Raison personnelle, voyage, besoin exceptionnel.

#     Remarques : Il doit être demandé et accepté par l’employeur.

# Les deux autres pour rappel :

#     ✅ maladie — Congé maladie : pour cause de maladie, généralement avec certificat médical.

#     ✅ exceptionnel — Congé exceptionnel : événements familiaux (mariage, décès, naissance, etc.).


# 🗂️ Répartition des types de congés à Madagascar
# | Type de congé    | Durée légale / standard              | Rémunération   | Certificat requis ? |
# | ---------------- | ------------------------------------ | -------------- | ------------------- |
# | **annuel**       | 2,5 jours ouvrables / mois           | ✅ Oui          | ❌ Non               |
# | **maladie**      | Jusqu’à 6 mois (souvent 1 mois payé) | ✅ Oui (limité) | ✅ Oui (obligatoire) |
# | **maternite**    | 14 semaines (98 jours)               | ✅ Oui          | ✅ Oui (médical)     |
# | **paternite**    | 3 jours ouvrés                       | ✅ Oui          | ❌ Optionnel         |
# | **sans\_solde**  | Variable (accord employeur)          | ❌ Non          | ❌ Non               |
# | **exceptionnel** | 1 à 3 jours selon événement          | ✅ Oui          | ❌ Non (sauf décès)  |
