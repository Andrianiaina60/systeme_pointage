
# employees/urls.py
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
    # Vues générales des employés
    path('', views.EmployeeListView.as_view(), name='employee-list'),
    path('<int:pk>/', views.EmployeeDetailView.as_view(), name='employee-detail'),
    path('toggle-status/', views.EmployeeToggleStatusView.as_view(), name='employee-toggle-status'),
    path('stats/', views.EmployeeStatsView.as_view(), name='employee-stats'),
    path('search/', views.EmployeeSearchView.as_view(), name='employee-search'),
    #liste empoyees par depertements
    path('by-department/<int:department_id>/', views.EmployeesByDepartmentView.as_view(), name='employees-by-department'),
    

 
    # Administration - Gestion des employés
 # Création d'un employé (admin uniquement)
    path('admin/employees/create/', AdminCreateEmployeeView.as_view(), name='admin-create-employee'),
    
    # Liste des employés (admin uniquement)
    path('admin/employees/', AdminListEmployeesView.as_view(), name='admin-list-employees'),
    
    # Détail d'un employé par son ID (admin uniquement) PUT,GET,DELETE DESACTIVATION
    path('admin/employees/<int:employee_id>/', AdminEmployeeDetailView.as_view(), name='admin-employee-detail'),
    
    # Activation / désactivation d'un employé (admin uniquement)
    path('admin/employees/toggle-status/', AdminToggleEmployeeStatusView.as_view(), name='admin-toggle-status'),
    
    # ############Mise à jour biométrique d'un employé (admin uniquement)
    path('admin/employees/<int:employee_id>/biometric/', AdminUpdateBiometricView.as_view(), name='admin-update-biometric'),
]