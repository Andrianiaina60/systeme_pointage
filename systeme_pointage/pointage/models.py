# pointage/models.py
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta

class Pointage(models.Model):
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='pointages')
    date = models.DateField(default=timezone.now)
    heure_entree = models.TimeField(blank=True, null=True)
    heure_sortie = models.TimeField(blank=True, null=True)

    temps_travaille = models.DurationField(blank=True, null=True)
    retard = models.DurationField(blank=True, null=True)
    heures_supplementaires = models.DurationField(blank=True, null=True)

    METHODE_CHOICES = [
        ('facial', 'Reconnaissance faciale'),
    ]
    methode_entree = models.CharField(max_length=20, choices=METHODE_CHOICES, default='facial')
    methode_sortie = models.CharField(max_length=20, choices=METHODE_CHOICES, default='facial')

    STATUS_CHOICES = [
        ('present', 'Présent'),
        ('absent', 'Absent'),
        ('retard', 'En retard'),
        ('conge', 'En congé'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')

    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'date']
        ordering = ['-date', '-heure_entree']

    def __str__(self):
        return f"{self.employee.nom} - {self.date}"

    def calculer_temps_travaille(self):
        if self.heure_entree and self.heure_sortie:
            entree = datetime.combine(self.date, self.heure_entree)
            sortie = datetime.combine(self.date, self.heure_sortie)
            if sortie < entree:
                sortie += timedelta(days=1)
            self.temps_travaille = sortie - entree
            if self.temps_travaille > timedelta(hours=8):
                self.heures_supplementaires = self.temps_travaille - timedelta(hours=8)
            self.save()