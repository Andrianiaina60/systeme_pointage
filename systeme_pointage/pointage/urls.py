from django.urls import path
from .views import ManagerDepartmentRetardsView
from .views import NotifyLateEmployeesView

from .views import (
    FacialCheckInView, FacialCheckOutView, PointageListView, PointageTodayView,
    AdminPointageListView, AdminPointageStatsView, AdminPointageReportsView,
    AdminEmployeeAttendanceView, AdminPointageNotificationsView,
    ManagerDepartmentPointagesView, AdminOrRHPointageStatsView
)

urlpatterns = [
    # Pointage employé
    path('checkin/', FacialCheckInView.as_view(), name='facial-checkin'),
    path('checkout/', FacialCheckOutView.as_view(), name='facial-checkout'),
    path('me/history/', PointageListView.as_view(), name='my-pointages'),
    path('me/today/', PointageTodayView.as_view(), name='my-today-pointage'),

    # Admin & RH
    path('admin/all/', AdminPointageListView.as_view(), name='admin-pointages'),
    path('admin/stats/', AdminPointageStatsView.as_view(), name='admin-stats'),
    path('admin/reports/', AdminPointageReportsView.as_view(), name='admin-reports'),
    path('admin/employee/<int:employee_id>/attendance/', AdminEmployeeAttendanceView.as_view(), name='admin-employee-attendance'),
    path('admin/notifications/', AdminPointageNotificationsView.as_view(), name='admin-pointage-notifications'),
    path('admin/retards/', AdminOrRHPointageStatsView.as_view(), name='admin-retards'),
    path('admin/notify-late/', NotifyLateEmployeesView.as_view(), name='notify-late-employees'),

    # Manager
    path('manager/department/', ManagerDepartmentPointagesView.as_view(), name='manager-department-pointages'),
    path('manager/retards/', ManagerDepartmentRetardsView.as_view(), name='manager-retards'),

]


    # regler heure pointage shell:
    #     from datetime import datetime
    # print(datetime.now())  # heure locale machine (UTC+1 si réglée ainsi)


# 🔸 Routes pour employé :
# | Méthode | URL            | Vue                  | Rôle(s) | Action                         |
# | ------- | -------------- | -------------------- | ------- | ------------------------------ |
# | `POST`  | `/checkin/`    | `FacialCheckInView`  | Tous    | Pointage d’entrée facial       |
# | `POST`  | `/checkout/`   | `FacialCheckOutView` | Tous    | Pointage de sortie facial      |
# | `GET`   | `/me/history/` | `PointageListView`   | Employé | Historique personnel           |
# | `GET`   | `/me/today/`   | `PointageTodayView`  | Employé | Pointage du jour (s’il existe) |

# 🔸 Routes pour admin & RH :
# | Méthode | URL                                               | Vue                              | Description                                 |
# | ------- | ------------------------------------------------- | -------------------------------- | ------------------------------------------- |
# | `GET`   | `/admin/all/`                                     | `AdminPointageListView`          | Tous les pointages                          |
# | `GET`   | `/admin/stats/`                                   | `AdminPointageStatsView`         | Statistiques générales                      |
# | `GET`   | `/admin/reports/?start=YYYY-MM-DD&end=YYYY-MM-DD` | `AdminPointageReportsView`       | Rapports personnalisés par date             |
# | `GET`   | `/admin/employee/<int:employee_id>/attendance/`   | `AdminEmployeeAttendanceView`    | Historique d’un employé                     |
# | `GET`   | `/admin/notifications/`                           | `AdminPointageNotificationsView` | Liste des absents + retardataires du jour   |
# | `GET`   | `/admin/retards/`                                 | `AdminOrRHPointageStatsView`     | Cumul des retards, sanctions, compensations |

# 🔸 Route pour manager :
# | Méthode | URL                    | Vue                              | Description                                      |
# | ------- | ---------------------- | -------------------------------- | ------------------------------------------------ |
# | `GET`   | `/manager/department/` | `ManagerDepartmentPointagesView` | Liste des pointages du jour pour son département |
