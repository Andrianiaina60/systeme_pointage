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
    path('', LeaveListView.as_view(), name='leave-list'),
    path('create/', LeaveCreateView.as_view(), name='leave-create'),
    path('<int:pk>/', LeaveDetailView.as_view(), name='leave-detail'),
    path('<int:pk>/rh-action/', RHLeaveActionView.as_view(), name='rh-action'),
    path('<int:pk>/manager-action/', ManagerLeaveActionView.as_view(), name='manager-action'),

    path('types/', LeaveTypeListView.as_view(), name='leave-types'),
    path('types/public/', LeaveTypePublicView.as_view(), name='leave-types-public'),

    path('stats/', LeaveStatsView.as_view(), name='leave-stats'),
    path('balance/me/', EmployeeOwnLeaveBalanceView.as_view(), name='leave-balance-me'),
    path('balance/', EmployeeLeaveBalanceView.as_view(), name='leave-balance'),
    path('balance/total/', LeaveBalanceView.as_view(), name='leave-balance-total'),
    path('calendar/', LeaveCalendarView.as_view(), name='leave-calendar'),
    path('export/', LeaveExportView.as_view(), name='leave-export'),
]
