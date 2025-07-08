from departments.models import Department
from employees.models import Employee
from authentication.models import Authentication

# Créer département
dep, created = Department.objects.get_or_create(
    nom="Informatique",
    defaults={"description": "Département IT"}
)

# Créer employé admin s'il n'existe pas
emp = Employee.objects.filter(immatricule="ADM001").first()
if not emp:
    emp = Employee(
        immatricule="ADM001",
        nom="Admin",
        prenom="Système",
        email="admin@gmail.com",
        telephone="0320000000",
        poste="Administrateur",
        departement=dep,
        is_active_employee=True,
    )
    emp.set_password("admin[1234]")
    emp.save()
    print("Employé admin créé")

# Créer compte authentication lié
auth = Authentication.objects.filter(employee=emp).first()
if not auth:
    auth = Authentication(
        employee=emp,
        email="admin@gmail.com",
        role="admin",
        is_active=True,
        is_staff=True,
        is_superuser=True,
    )
    auth.set_password("admin[1234]")
    auth.save()
    print("Compte admin Authentication créé")

print("Admin prêt à être utilisé")
