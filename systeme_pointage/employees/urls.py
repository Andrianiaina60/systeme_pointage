from django.urls import path
from . import views
from employees.views import (
    AdminCreateEmployeeView,
    AdminListEmployeesView,
    AdminEmployeeDetailView,
    AdminToggleEmployeeStatusView,
    AdminUpdateBiometricView,
)

app_name = 'employees'

urlpatterns = [
    # Vues générales accessibles aux Admin, RH, Manager

    # 🔹 GET /api/employees/
    # ✅ Admin, RH, Manager
    # Liste tous les employés (avec pagination et filtres possibles)
    path('', views.EmployeeListView.as_view(), name='employee-list'),

    # 🔹 GET /api/employees/<id>/
    # ✅ Admin, RH, Manager, Employé (uniquement son propre profil)
    # Détail d’un employé spécifique
    path('<int:pk>/', views.EmployeeDetailView.as_view(), name='employee-detail'),

    # 🔹 GET /api/employees/stats/
    # ✅ Admin uniquement
    # Statistiques globales (total, actifs, inactifs)
    path('stats/', views.EmployeeStatsView.as_view(), name='employee-stats'),

    # 🔹 GET /api/employees/by-department/<department_id>/
    # ✅ Admin, RH, Manager
    # Liste des employés d’un département donné
    path('by-department/<int:department_id>/', views.EmployeesByDepartmentView.as_view(), name='employees-by-department'),

    # 🔹 GET /api/employees/search/?q=...
    # ✅ Admin, RH, Manager
    # Recherche d’employés par nom, prénom, email, immatricule
    path('search/', views.EmployeeSearchView.as_view(), name='employee-search'),

    # Routes d’administration, accessibles uniquement aux Admin

    # 🔹 POST /api/employees/admin/employees/create/
    # Création d’un employé
    path('admin/employees/create/', AdminCreateEmployeeView.as_view(), name='admin-create-employee'),

    # 🔹 GET /api/employees/admin/employees/
    # Liste complète des employés pour l’admin
    path('admin/employees/', AdminListEmployeesView.as_view(), name='admin-list-employees'),

    # 🔹 GET, PUT, DELETE /api/employees/admin/employees/<employee_id>/
    # Détail, modification et suppression d’un employé (activation/désactivation)
    path('admin/employees/<int:employee_id>/', AdminEmployeeDetailView.as_view(), name='admin-employee-detail'),

    # 🔹 POST /api/employees/admin/employees/toggle-status/
    # Activation/désactivation d’un employé
    path('admin/employees/toggle-status/', AdminToggleEmployeeStatusView.as_view(), name='admin-toggle-status'),

    # 🔹 PUT /api/employees/admin/employees/<employee_id>/biometric/
    # Mise à jour des données biométriques d’un employé
    path('admin/employees/<int:employee_id>/biometric/', AdminUpdateBiometricView.as_view(), name='admin-update-biometric'),
]
