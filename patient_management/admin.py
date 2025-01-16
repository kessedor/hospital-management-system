from django.contrib import admin
from .models import Admission, MedicalRecord

@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = ('patient', 'admission_date', 'admission_type', 'status', 'ward', 'primary_doctor')
    search_fields = ('patient__patient_id', 'patient__user__first_name', 'patient__user__last_name', 'ward')
    list_filter = ('status', 'admission_type', 'ward')
    fieldsets = (
        ('Basic Information', {
            'fields': ('patient', 'hospital', 'admission_date', 'admission_type', 'status')
        }),
        ('Location', {
            'fields': ('ward', 'bed_number')
        }),
        ('Medical Staff', {
            'fields': ('primary_doctor', 'attending_nurses')
        }),
        ('Discharge Information', {
            'fields': ('discharge_date', 'discharge_notes', 'discharge_diagnosis')
        }),
        ('Additional Information', {
            'fields': ('chief_complaint', 'notes')
        })
    )

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ['patient', 'created_at', 'doctor', 'diagnosis']
    search_fields = ['patient__patient_id', 'patient__user__first_name', 
                    'patient__user__last_name', 'diagnosis', 'treatment']
    list_filter = ['created_at', 'doctor', 'hospital']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    fieldsets = [
        ('Patient Information', {
            'fields': ['patient', 'hospital', 'doctor']
        }),
        ('Vital Signs', {
            'fields': [
                'temperature', 'blood_pressure', 'pulse_rate',
                'respiratory_rate', 'weight', 'height', 'oxygen_saturation'
            ]
        }),
        ('Medical Details', {
            'fields': ['symptoms', 'diagnosis', 'treatment', 'prescription', 'notes']
        }),
        ('Follow-up', {
            'fields': ['follow_up_date', 'follow_up_notes']
        }),
        ('Additional Information', {
            'fields': ['lab_results', 'attachments']
        }),
        ('Record History', {
            'fields': ['created_by', 'created_at', 'updated_by', 'updated_at', 'update_notes'],
            'classes': ['collapse']
        })
    ]

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new record
            obj.created_by = request.user
        else:  # If updating existing record
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)