from django.urls import path
from . import views

app_name = 'patient_management'

urlpatterns = [
    path('test/', lambda request: HttpResponse("Patient management is working"), name='test'),
    # Dashboard
    path('dashboard/', views.dashboard, name='patient_dashboard'),
    
    # Patient Management URLs
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/create/', views.patient_create, name='patient_create'),
    path('patients/<int:pk>/', views.patient_detail, name='patient_detail'),
    path('patients/<int:pk>/update/', views.patient_update, name='patient_update'),
    path('patients/<int:pk>/delete/', views.patient_delete, name='patient_delete'),
    path('patients/<int:pk>/edit/', views.patient_update, name='patient_edit'),
    
    # Medical Records URLs
    path('patients/<int:patient_id>/medical-records/', 
         views.medical_record_list, name='medical_record_list'),
    path('patients/<int:patient_id>/medical-records/create/', 
         views.medical_record_create, name='medical_record_create'),
    path('patients/<int:patient_id>/medical-records/<int:record_id>/', 
         views.medical_record_detail, name='medical_record_detail'),
    path('patients/<int:patient_id>/medical-records/<int:record_id>/update/', 
         views.medical_record_update, name='medical_record_update'),
    
    # Lab Results URLs (nested under Medical Records)
    path('medical-records/<int:medical_record_id>/lab-results/create/', 
         views.lab_result_create, name='lab_result_create'),
    path('lab-results/<int:pk>/', 
         views.lab_result_detail, name='lab_result_detail'),
    
    # Admission Management URLs
    path('admissions/', views.admission_list, name='admission_list'),
    path('admissions/create/', views.admission_create, name='admission_create'),
    path('admissions/<int:pk>/', views.admission_detail, name='admission_detail'),

    # Appointment Management URLs
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/create/', views.appointment_create, name='appointment_create'),
    path('appointments/<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/<int:pk>/update/', views.appointment_update, name='appointment_update'),
    path('appointments/<int:pk>/cancel/', views.appointment_cancel, name='appointment_cancel'),
]