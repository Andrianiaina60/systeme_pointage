# Generated by Django 4.2.7 on 2025-06-18 09:32

import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("departments", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="Employee",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "first_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="first name"
                    ),
                ),
                (
                    "last_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="last name"
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        blank=True, max_length=254, verbose_name="email address"
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                        verbose_name="active",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date joined"
                    ),
                ),
                ("immatricule", models.CharField(max_length=20, unique=True)),
                ("nom", models.CharField(max_length=100)),
                ("prenom", models.CharField(default="", max_length=100)),
                ("telephone", models.CharField(blank=True, max_length=20, null=True)),
                ("poste", models.CharField(max_length=100)),
                (
                    "photo",
                    models.ImageField(
                        blank=True, null=True, upload_to="employee_photos/"
                    ),
                ),
                ("face_encoding", models.TextField(blank=True, null=True)),
                ("is_active_employee", models.BooleanField(default=True)),
                ("date_embauche", models.DateField(auto_now_add=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("username", models.CharField(blank=True, max_length=20, unique=True)),
                (
                    "departement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="employees",
                        to="departments.department",
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Les groupes auxquels cet employé appartient.",
                        related_name="employees_groups",
                        related_query_name="employee",
                        to="auth.group",
                        verbose_name="groupes",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Permissions spécifiques pour cet employé.",
                        related_name="employees_permissions",
                        related_query_name="employee",
                        to="auth.permission",
                        verbose_name="permissions utilisateur",
                    ),
                ),
            ],
            options={
                "verbose_name": "Employé",
                "verbose_name_plural": "Employés",
                "db_table": "employee",
            },
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
    ]
