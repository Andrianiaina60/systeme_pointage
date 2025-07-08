# authentication/urls.py
from django.urls import path
from . import views


urlpatterns = [
    # Authentification générale
    path('login/', views.LoginView.as_view(), name='login'),
    path('login/facial/', views.FacialLoginView.as_view(), name='facial-login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/update/', views.ProfileUpdateView.as_view(), name='profile-update'),
]