from django.urls import path
from . import views

urlpatterns = [
    # 🔹 GET /api/departments/
    # Affiche la liste de tous les départements (accessible à tout utilisateur authentifié)
    path('departments/', views.DepartmentListView.as_view(), name='department-list'),

    # 🔹 POST /api/departments/create/
    # Créer un nouveau département (réservé aux administrateurs)
    path('create/', views.DepartmentCreateView.as_view(), name='department-create'),

    # 🔹 GET /api/departments/<id>/
    # Récupérer les détails d’un département spécifique (accessible à tout utilisateur authentifié)
    # 🔹 PUT /api/departments/<id>/
    # Modifier les informations d’un département (réservé aux administrateurs)
    # 🔹 DELETE /api/departments/<id>/
    # Supprimer un département s’il n’a pas d’employés (réservé aux administrateurs)
    path('<int:pk>/', views.DepartmentDetailView.as_view(), name='department-detail'),

    # 🔹 GET /api/departments/<id>/stats/
    # Obtenir les statistiques d’un département :
    # - Nombre total d’employés
    # - Nombre d’actifs/inactifs
    # - Nombre de congés approuvés en coursKs
    path('<int:pk>/stats/', views.DepartmentStatsView.as_view(), name='department-stats'),
]


# | Méthode | URL                         | Description                 |
# | ------- | --------------------------- | --------------------------- |
# | GET     | `/api/departments/`         | Liste des départements      |
# | POST    | `/api/departments/create/`  | Création (admin uniquement) |
# | GET     | `/api/departments/3/`       | Détails d’un département    |
# | PUT     | `/api/departments/3/`       | Modification (admin)        |
# | DELETE  | `/api/departments/3/`       | Suppression (admin)         |
# | GET     | `/api/departments/3/stats/` | Statistiques et congés      |
