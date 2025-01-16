from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.home, name='home'),
    path('hospitals/', views.hospital_search, name='hospital_search'),
    path('hospitals/<int:hospital_id>/', views.hospital_detail, name='hospital_detail'),
    path('hospitals/<int:hospital_id>/book/', views.book_appointment, name='book_appointment'),
    path('appointment/<int:appointment_id>/confirmation/', 
         views.appointment_confirmation, name='appointment_confirmation'),
    path('my-appointments/', views.my_appointments, name='my_appointments'),
    path('appointment/<int:appointment_id>/cancel/', 
         views.cancel_appointment, name='cancel_appointment'),
    path('my-profile/', views.my_profile, name='my_profile'),
]