from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
import os

class Employee(AbstractUser):
    immatricule = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100, default='')
    adresse = models.CharField(max_length=255, blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    poste = models.CharField(max_length=100)
    departement = models.ForeignKey('departments.Department', on_delete=models.CASCADE, related_name='employees')

    photo = models.ImageField(upload_to='employee_photos/', blank=True, null=True)
    face_encoding = models.JSONField(null=True, blank=True)

    is_active_employee = models.BooleanField(default=True)
    date_embauche = models.DateField(auto_now_add=True)

    # 🔽 Ajout pour le suivi des congés
    solde_conge_annuel = models.PositiveIntegerField(default=30)  # ← 🟢 Ajout important

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Username personnalisé = matricule
    username = models.CharField(max_length=20, unique=True, blank=True)

    groups = models.ManyToManyField(
        Group,
        related_name='employees_groups',
        blank=True,
        help_text='Les groupes auxquels cet employé appartient.',
        verbose_name='groupes',
        related_query_name='employee',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='employees_permissions',
        blank=True,
        help_text='Permissions spécifiques pour cet employé.',
        verbose_name='permissions utilisateur',
        related_query_name='employee',
    )

    class Meta:
        db_table = 'employee'
        verbose_name = 'Employé'
        verbose_name_plural = 'Employés'

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.immatricule
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.immatricule} - {self.nom} {self.prenom}"

    def delete_photo(self):
        if self.photo and os.path.isfile(self.photo.path):
            os.remove(self.photo.path)
