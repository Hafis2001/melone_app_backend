from django.urls import path
from .views import (
    OwnerRegisterView, OwnerLoginView,
    StaffCreateView, StaffListView, StaffToggleView,
    StaffLoginView, SyncOrdersView,
    OwnerOrdersView, OwnerRevenueView
)

urlpatterns = [
    # Owner Endpoints
    path('owner/register/', OwnerRegisterView.as_view(), name='owner-register'),
    path('owner/login/', OwnerLoginView.as_view(), name='owner-login'),
    
    # Staff Management (by Owner)
    path('owner/staff/create/', StaffCreateView.as_view(), name='staff-create'),
    path('owner/staff/', StaffListView.as_view(), name='staff-list'),
    path('owner/staff/<int:staff_id>/toggle/', StaffToggleView.as_view(), name='staff-toggle'),
    
    # Data Retrieval (by Owner)
    path('owner/orders/', OwnerOrdersView.as_view(), name='owner-orders'),
    path('owner/revenue/', OwnerRevenueView.as_view(), name='owner-revenue'),
    
    # Staff Endpoints
    path('staff/login/', StaffLoginView.as_view(), name='staff-login'),
    
    # Sync
    path('sync/', SyncOrdersView.as_view(), name='sync-orders'),
]
