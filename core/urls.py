from django.urls import path
from . import views

urlpatterns = [
    # Existing URLs
    path('', views.public_homepage, name='public_homepage'),
    path('dashboard/', views.hospital_dashboard, name='hospital_dashboard'),
    
    # Staff Management URLs
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/create/', views.staff_create, name='staff_create'),
    path('staff/<str:employee_id>/', views.staff_detail, name='staff_detail'),
    path('staff/<str:employee_id>/edit/', views.staff_update, name='staff_update'),
    path('staff/<str:employee_id>/delete/', views.staff_delete, name='staff_delete'),

    # Schedule Management URLs
    path('schedule/', views.schedule_list, name='schedule_list'),
    path('schedule/create/', views.schedule_create, name='schedule_create'),
    path('schedule/weekly/', views.schedule_weekly, name='schedule_weekly'),
    path('schedule/export/', views.schedule_export, name='schedule_export'),
    
    # Leave Management URLs
    path('leave/', views.leave_list, name='leave_list'),
    path('leave/request/', views.leave_request, name='leave_request'),
    path('leave/<int:pk>/approve/', views.leave_approve, name='leave_approve'),
    path('leave/<int:pk>/reject/', views.leave_reject, name='leave_reject'),

    # Dashboard Action URLs
    path('update-beds/', views.update_bed_availability, name='update_bed_availability'),
    path('toggle-emergency/', views.toggle_emergency_status, name='toggle_emergency_status'),
]