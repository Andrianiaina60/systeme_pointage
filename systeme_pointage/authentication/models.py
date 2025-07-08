from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from employees.models import Employee

class AuthenticationManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est requise")
        if 'employee' not in extra_fields or extra_fields['employee'] is None:
            raise ValueError("Le champ 'employee' est obligatoire.")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(email, password, **extra_fields)

class Authentication(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('manager', 'Chef de département'),
        ('rh', 'RH'),
        ('employee', 'Employé'),
    ]

    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='auth_user')
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_created = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['employee']

    objects = AuthenticationManager()

    class Meta:
        db_table = 'authentication'
        verbose_name = 'Authentification'
        verbose_name_plural = 'Authentifications'

    def __str__(self):
        return f"{self.email} ({self.role}) - {self.employee.nom}"

    @property
    def is_manager(self):
        return self.role == 'manager'

    @property
    def is_rh(self):
        return self.role == 'rh'









# from django.db import models
# from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
# from django.utils import timezone
# from employees.models import Employee

# class AuthenticationManager(BaseUserManager):
#     def create_user(self, email, password=None, **extra_fields):
#         if not email:
#             raise ValueError("L'adresse email est requise")
#         if 'employee' not in extra_fields or extra_fields['employee'] is None:
#             raise ValueError("Le champ 'employee' est obligatoire.")

#         email = self.normalize_email(email)
#         user = self.model(email=email, **extra_fields)

#         user.set_password(password)
#         user.save(using=self._db)
#         return user

#     def create_superuser(self, email, password=None, **extra_fields):
#         extra_fields.setdefault('role', 'admin')
#         extra_fields.setdefault('is_staff', True)
#         extra_fields.setdefault('is_superuser', True)
#         extra_fields.setdefault('is_active', True)

#         return self.create_user(email, password, **extra_fields)

# class Authentication(AbstractBaseUser, PermissionsMixin):
#     ROLE_CHOICES = [
#         ('admin', 'Administrateur'),
#         ('manager', 'Chef de département'),
#         ('rh', 'RH'),
#         ('employee', 'Employé'),
#     ]

#     employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='auth_user')
#     email = models.EmailField(unique=True)
#     role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
#     is_active = models.BooleanField(default=True)
#     is_staff = models.BooleanField(default=False)
#     date_created = models.DateTimeField(default=timezone.now)
#     last_login = models.DateTimeField(null=True, blank=True)

#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = ['employee']

#     objects = AuthenticationManager()

#     class Meta:
#         db_table = 'authentication'
#         verbose_name = 'Authentification'
#         verbose_name_plural = 'Authentifications'

#     def __str__(self):
#         return f"{self.email} ({self.role}) - {self.employee.nom}"



