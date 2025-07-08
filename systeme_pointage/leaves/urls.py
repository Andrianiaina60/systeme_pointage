# leaves/urls.py

from django.urls import path

from .views import (
    LeaveListView,
    LeaveCreateView,
    LeaveDetailView,
    LeaveActionView,
    RHLeaveActionView,
    ManagerLeaveActionView,
    LeaveApprovalView,
    LeaveStatsView,
    LeaveExportView,
    LeaveBalanceView,
    LeaveCalendarView,
    EmployeeLeaveBalanceView,
    EmployeeOwnLeaveBalanceView,
    LeaveTypeListView,
    LeaveTypePublicView,
)

from employees.views import EmployeeListView  # si besoin, sinon à retirer

urlpatterns = [
    # Congés employés - CRUD & listing
    path('', LeaveListView.as_view(), name='leave-list'),
    path('create/', LeaveCreateView.as_view(), name='leave-create'),
    path('my-leaves/', LeaveListView.as_view(), name='my-leaves'),  # filtre en vue selon user

    path('<int:pk>/', LeaveDetailView.as_view(), name='leave-detail'),

    # Types de congés
    path('leave/types/', LeaveTypeListView.as_view(), name='leave-types'),              # auth requis
    path('leave/types/public/', LeaveTypePublicView.as_view(), name='leave-types-public'),  # accès libre

    # Employé connecté - Voir son propre solde de congés (GET)
    path('leave-balances/me/', EmployeeOwnLeaveBalanceView.as_view(), name='employee-own-leave-balance'),

    # Admin - Approuver ou rejeter une demande de congé individuelle (POST)
    path('admin/action/<int:pk>/', LeaveActionView.as_view(), name='admin-leave-action'),

    # RH - Approuver ou rejeter une demande déjà validée par un manager (POST)
    path('rh/action/<int:pk>/', RHLeaveActionView.as_view(), name='rh-leave-action'),

    # Manager - Valider ou refuser une demande de congé d’un employé de son département (POST)
    path('manager/action/<int:pk>/', ManagerLeaveActionView.as_view(), name='manager-leave-action'),

    # Admin/RH - Voir les soldes de congés de tous les employés (GET)
    path('leave-balances/', LeaveBalanceView.as_view(), name='admin-leave-balances'),


    # ADMIN
   # Admin - Voir tous les congés (GET)
    path('admin/all/', LeaveListView.as_view(), name='admin-all-leaves'),

    # Admin - Voir les congés en attente (GET)
    path('admin/pending/', LeaveListView.as_view(), name='admin-pending-leaves'),

    # Admin - Approuver ou rejeter plusieurs demandes en une seule fois (POST)
    path('admin/approve-batch/', LeaveApprovalView.as_view(), name='admin-approve-batch'),

    # Admin - Statistiques sur les congés : total, approuvés, rejetés... (GET)
    path('admin/stats/', LeaveStatsView.as_view(), name='admin-leave-stats'),

    # Admin - Exporter tous les congés au format CSV (GET)
    path('admin/export/', LeaveExportView.as_view(), name='admin-leave-export'),

    # Admin - Consulter le solde total de congés d’un ou plusieurs employés (GET)
    path('admin/balance/', LeaveBalanceView.as_view(), name='admin-leave-balance'),

    # Admin - Affichage calendrier des congés par date de début (GET)
    path('admin/calendar/', LeaveCalendarView.as_view(), name='admin-leave-calendar'),

]



# # api disponible
# Routes employé (utilisateur connecté)
# | Méthode        | URL                      | Description                                                |
# | -------------- | ------------------------ | ---------------------------------------------------------- |
# | GET            | `/api/leaves/`           | Liste ses propres demandes de congé                        |
# | POST           | `/api/leaves/create/`    | Créer une nouvelle demande                                 |
# | GET/PUT/DELETE | `/api/leaves/<pk>/`      | Détail, modification, suppression d’une demande spécifique |
# | GET            | `/api/leaves/my-leaves/` | Alias pour ses congés (idem `/api/leaves/`)                |
# | GET            | `/api/leaves/stats/`     | Statistiques personnelles (ex: nombre de jours posés)      |
# | GET            | `/api/leaves/balance/`   | Solde personnel de congés                                  |
# | GET            | `/api/leaves/calendar/`  | Vue calendrier personnel                                   |

# Routes administration (admin uniquement)
# | Méthode | URL                                | Description                         |
# | ------- | ---------------------------------- | ----------------------------------- |
# | GET     | `/api/leaves/admin/all/`           | Liste complète des demandes congés  |
# | GET     | `/api/leaves/admin/pending/`       | Liste des congés en attente         |
# | POST    | `/api/leaves/admin/approve-batch/` | Approuver plusieurs demandes en lot |
# | GET     | `/api/leaves/admin/reports/`       | Rapports détaillés des congés       |
# | GET     | `/api/leaves/admin/stats/`         | Statistiques globales des congés    |
# | GET     | `/api/leaves/admin/export/`        | Export des données congés           |
# | GET     | `/api/leaves/admin/balance/`       | Solde de congés des employés        |
# | GET     | `/api/leaves/admin/calendar/`      | Calendrier des congés global        |


# # ✅ Rôles, Accès et Actions dans le Système de Gestion de Congé
# | Rôle              | Accès aux vues | Actions possibles                                                                                                                                                                    |
# | ----------------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
# | 🛠 **Admin**      | `/admin/...`   | - Visualiser toutes les demandes de congé (tous statuts)<br>- Approuver / rejeter toute demande<br>- Suivre tout l’historique<br>- Accéder aux statistiques et exports               |
# | 👩‍💼 **RH**      | `/rh/...`      | - Visualiser **toutes les demandes des employés**, tous statuts<br>- Approuver ou rejeter une demande<br>- Ajouter un commentaire RH<br>- **Suivre l’historique complet**            |
# | 👨‍💼 **Manager** | `/manager/...` | - Visualiser les demandes de **son département**, tous statuts<br>- Valider ou refuser une demande (niveau 1)<br>- Ajouter un commentaire<br>- **Suivre l’historique de son équipe** |
