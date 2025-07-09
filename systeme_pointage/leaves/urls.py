from django.urls import path
from .views import (
    LeaveCreateView, LeaveListView, LeaveDetailView,
    LeaveTypeListView, LeaveTypePublicView,
    RHLeaveActionView, ManagerLeaveActionView,
    LeaveStatsView, EmployeeOwnLeaveBalanceView,
    EmployeeLeaveBalanceView, LeaveBalanceView,
    LeaveCalendarView, LeaveExportView,
)

urlpatterns = [
    # 🔍 Liste des congés (GET) - accès filtré selon rôle (admin, rh, manager, employé)
    path('', LeaveListView.as_view(), name='leave-list'),

    # 📝 Créer une demande de congé (POST) - réservé à l'employé connecté
    path('create/', LeaveCreateView.as_view(), name='leave-create'),

    # 🔍/✏️/🗑️ Détail, modification ou suppression d’une demande de congé (GET, PUT, DELETE)
    # Seul le propriétaire peut modifier/supprimer si en attente
    path('<int:pk>/', LeaveDetailView.as_view(), name='leave-detail'),

    # ✅❌ Action RH (POST) - approuver ou rejeter une demande déjà validée par le manager
    path('<int:pk>/rh-action/', RHLeaveActionView.as_view(), name='rh-action'),

    # ✅❌ Action Manager (POST) - approuver ou rejeter une demande de son département
    path('<int:pk>/manager-action/', ManagerLeaveActionView.as_view(), name='manager-action'),

    # 📄 Liste des types de congés (GET) - pour les utilisateurs connectés
    path('types/', LeaveTypeListView.as_view(), name='leave-types'),

    # 📄 Liste publique des types de congés (GET) - accessible sans authentification
    path('types/public/', LeaveTypePublicView.as_view(), name='leave-types-public'),

    # 📊 Statistiques globales sur les congés (GET) - admin, RH, ou employé (filtré)
    path('stats/', LeaveStatsView.as_view(), name='leave-stats'),

    # 🧾 Solde de congés personnel de l'utilisateur connecté (GET)
    path('balance/me/', EmployeeOwnLeaveBalanceView.as_view(), name='leave-balance-me'),

    # 🧾 Solde de congés par employé (GET) - pour RH/admin, ou soi-même
    path('balance/', EmployeeLeaveBalanceView.as_view(), name='leave-balance'),

    # 🧾 Solde total des congés approuvés (GET) - admin/RH/employé
    path('balance/total/', LeaveBalanceView.as_view(), name='leave-balance-total'),

    # 📅 Calendrier des congés (GET) - pour affichage sous forme calendrier
    path('calendar/', LeaveCalendarView.as_view(), name='leave-calendar'),

    # 📤 Exporter les congés en CSV (GET) - réservé à l’admin ou RH
    path('export/', LeaveExportView.as_view(), name='leave-export'),
]
