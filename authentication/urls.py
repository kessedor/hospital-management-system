from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'authentication'

urlpatterns = [
    # Authentication views
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('hospital-dashboard/', views.hospital_dashboard, name='hospital_dashboard'),
    
    # Gmail OAuth2 URLs (new)
    path('gmail-auth/', views.gmail_auth_init, name='gmail_auth_init'),
    path('oauth2callback/', views.oauth2callback, name='oauth2callback'),
    
    # Staff Management
    path('staff/', views.staff_management, name='staff_management'),
    path('staff/add/', views.add_staff_member, name='add_staff_member'),
    path('staff/edit/<int:staff_id>/', views.edit_staff_member, name='edit_staff_member'),
    path('staff/delete/<int:staff_id>/', views.delete_staff_member, name='delete_staff_member'),
    
    # Email verification
    path('activate/<str:uidb64>/<str:token>/', 
     views.activate_account, 
     name='activate'),
    
    # Hospital registration and management
    path('hospital-signup/', views.hospital_signup_view, name='hospital_signup'),
    path('patient-signup/', views.patient_signup_view, name='patient_signup'), 
    path('update-bed-availability/', views.update_bed_availability, name='update_bed_availability'),
    path('toggle-emergency-status/', views.toggle_emergency_status, name='toggle_emergency_status'),
       
    # Inventory management
    path('inventory/', views.inventory_management, name='inventory_management'),
    path('inventory/add/', views.add_inventory_item, name='add_inventory_item'),
    path('inventory/edit/<int:item_id>/', views.edit_inventory_item, name='edit_inventory_item'),
    path('inventory/stock/<int:item_id>/', views.update_inventory_stock, name='update_inventory_stock'),
    path('inventory/delete/<int:item_id>/', views.delete_inventory_item, name='delete_inventory_item'),
    path('inventory/stats/', views.get_inventory_stats, name='get_inventory_stats'),
    
    # Appointments management
    path('appointments/', views.hospital_appointments, name='hospital_appointments'),
    path('appointments/<int:appointment_id>/update/', 
         views.update_appointment_status, name='update_appointment_status'),
    path('appointments/calendar/', views.appointment_calendar, name='appointment_calendar'),
    
    # Password reset
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='authentication/password_reset.html'),
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='authentication/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='authentication/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='authentication/password_reset_complete.html'),
         name='password_reset_complete'),
    
    # Profile management
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/change-password/', views.change_password_view, name='change_password'),
]