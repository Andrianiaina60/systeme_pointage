from django.urls import path
from . import views

urlpatterns = [
    # 🔵 Pointage d’entrée et sortie par reconnaissance faciale pour l’employé connecté
    path('checkin/', views.FacialCheckInView.as_view(), name='facial-checkin'),
    path('checkout/', views.FacialCheckOutView.as_view(), name='facial-checkout'),

    # CONSULTATION DES POINTAGE
    # 🟢 Affiche tout l’historique des pointages le pointage du jour de l’employé connecté
    path('me/history/', views.PointageListView.as_view(), name='my-pointages'),
    path('me/today/', views.PointageTodayView.as_view(), name='my-today-pointage'),

    # ADMIN
    # 🟡 Pour l’admin : liste complète de tous les pointages
    path('admin/all/', views.AdminPointageListView.as_view(), name='admin-pointages'),

    # 🟡 Pour l’admin : statistiques globales (retards, absents, total du jour)
    path('admin/stats/', views.AdminPointageStatsView.as_view(), name='admin-stats'),

    # 🟡 Pour l’admin : rapports filtrables sur les pointages (avec date début et fin)
    path('admin/reports/', views.AdminPointageReportsView.as_view(), name='admin-reports'),

    # 🟡 Pour l’admin : vue détaillée de l’assiduité d’un employé spécifique
    path('admin/employee/<int:employee_id>/attendance/', views.AdminEmployeeAttendanceView.as_view(), name='admin-employee-attendance'),

    # 🔔 Pour l’admin : liste des absents et des retardataires du jour (hors congés)
    path('admin/notifications/', views.AdminPointageNotificationsView.as_view(), name='admin-pointage-notifications'),
]


# ✅ Fonctionnement actuel : clair et correct

# | Endpoint                                       | Vue                              | Description                              |
# | ---------------------------------------------- | -------------------------------- | ---------------------------------------- |
# | `GET /admin/all/`                              | `AdminPointageListView`          | Liste de tous les pointages              |
# | `GET /admin/stats/`                            | `AdminPointageStatsView`         | Stats globales (total, retards, absents) |
# | `GET /admin/reports/?start=YYYY-MM-DD&end=...` | `AdminPointageReportsView`       | Rapport filtré par date                  |
# | `GET /admin/employee/<id>/attendance/`         | `AdminEmployeeAttendanceView`    | Historique pointages d’un employé        |
# | `GET /admin/notifications/`                    | `AdminPointageNotificationsView` | Absents + Retards du jour (hors congés)  |

# | Endpoint           | Vue                  | Description             |
# | ------------------ | -------------------- | ----------------------- |
# | `POST /checkin/`   | `FacialCheckInView`  | Enregistre l’entrée     |
# | `POST /checkout/`  | `FacialCheckOutView` | Enregistre la sortie    |
# | `GET /me/history/` | `PointageListView`   | Historique complet      |
# | `GET /me/today/`   | `PointageTodayView`  | Pointage du jour actuel |


# ✅ Ce que tu gères très bien déjà :

#     ✅ Pointage unique par jour et par employé

#     ✅ Calcul automatique de retard, temps_travaille, heures_supplementaires

#     ✅ Méthode calculer_temps_travaille() intégrée dans le modèle

#     ✅ unique_together = ['employee', 'date'] : empêche les doublons