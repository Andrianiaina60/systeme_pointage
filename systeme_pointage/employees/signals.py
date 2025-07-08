from django.db.models.signals import post_save
from django.dispatch import receiver
from employees.models import Employee
from authentication.models import Authentication

@receiver(post_save, sender=Employee)
def sync_auth_role(sender, instance, **kwargs):
    try:
        auth = Authentication.objects.get(employee=instance)
        new_role = 'manager' if instance.poste.lower() == 'manager' else 'employee'
        if auth.role != new_role:
            auth.role = new_role
            auth.save()
    except Authentication.DoesNotExist:
        pass
