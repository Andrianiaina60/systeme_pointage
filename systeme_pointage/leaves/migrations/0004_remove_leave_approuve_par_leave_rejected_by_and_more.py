# Generated by Django 4.2.7 on 2025-07-09 13:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("employees", "0003_employee_solde_conge_annuel_and_more"),
        ("leaves", "0003_alter_leave_status_conge"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="leave",
            name="approuve_par",
        ),
        migrations.AddField(
            model_name="leave",
            name="rejected_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="rejected_leaves",
                to="employees.employee",
            ),
        ),
        migrations.AddField(
            model_name="leave",
            name="validated_by_manager",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="validated_leaves_by_manager",
                to="employees.employee",
            ),
        ),
        migrations.AddField(
            model_name="leave",
            name="validated_by_rh",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="validated_leaves_by_rh",
                to="employees.employee",
            ),
        ),
    ]
