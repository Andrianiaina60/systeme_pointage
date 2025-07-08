# departments/models.py

from django.db import models
from employees.models import Employee

class Department(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    manager = models.ForeignKey(
        Employee,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='managed_departments'
    )

    class Meta:
        db_table = 'department'
        verbose_name = 'Département'
        verbose_name_plural = 'Départements'

    def __str__(self):
        return self.nom






