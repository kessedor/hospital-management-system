from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import date
from authentication.models import Hospital, Staff, Patient

class Admission(models.Model):
    ADMISSION_TYPE_CHOICES = [
        ('EMERGENCY', 'Emergency'),
        ('PLANNED', 'Planned'),
        ('TRANSFER', 'Transfer')
    ]
    
    ADMISSION_STATUS = [
        ('ADMITTED', 'Admitted'),
        ('DISCHARGED', 'Discharged'),
        ('TRANSFERRED', 'Transferred')
    ]

    patient = models.ForeignKey(
        'authentication.Patient', 
        on_delete=models.CASCADE, 
        related_name='patient_admissions'
    )
    hospital = models.ForeignKey(
        'authentication.Hospital', 
        on_delete=models.CASCADE,
        related_name='hospital_admissions'
    )
    admission_date = models.DateTimeField()
    admission_type = models.CharField(max_length=20, choices=ADMISSION_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=ADMISSION_STATUS, default='ADMITTED')
    ward = models.CharField(max_length=50, blank=True, null=True)
    bed_number = models.CharField(max_length=10, blank=True, null=True)
    primary_doctor = models.ForeignKey(
        'authentication.Staff', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='doctor_admissions'
    )
    attending_nurses = models.ManyToManyField(
        'authentication.Staff',
        related_name='nurse_admissions',
        blank=True,
        limit_choices_to={'role': 'NURSE'}
    )
    discharge_date = models.DateTimeField(blank=True, null=True)
    discharge_notes = models.TextField(blank=True, null=True)
    discharge_diagnosis = models.TextField(blank=True, null=True)
    chief_complaint = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-admission_date']
    
    def __str__(self):
        return f"{self.patient.patient_id} - {self.admission_date.strftime('%Y-%m-%d')}"
    
    def get_duration(self):
        if self.discharge_date:
            return self.discharge_date - self.admission_date
        return timezone.now() - self.admission_date

class MedicalRecord(models.Model):
    # Basic fields
    patient = models.ForeignKey(
        'authentication.Patient', 
        on_delete=models.PROTECT,
        related_name='medical_records'
    )
    hospital = models.ForeignKey(
        'authentication.Hospital',
        on_delete=models.PROTECT,
        related_name='hospital_records'
    )
    doctor = models.ForeignKey(
        'authentication.Staff',
        on_delete=models.PROTECT,
        related_name='doctor_records'
    )
    
    # Vital Signs
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    blood_pressure = models.CharField(max_length=15, blank=True, null=True)
    pulse_rate = models.IntegerField(null=True, blank=True)
    respiratory_rate = models.IntegerField(null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    oxygen_saturation = models.IntegerField(null=True, blank=True)
    
    # Visit Details
    symptoms = models.TextField(blank=True, null=True)
    diagnosis = models.TextField(blank=True, null=True)
    treatment = models.TextField(blank=True, null=True)
    prescription = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # Lab Results and Attachments
    lab_results = models.JSONField(null=True, blank=True)
    attachments = models.FileField(
        upload_to='medical_records/',
        null=True,
        blank=True,
        help_text="Upload relevant documents (max 10MB)"
    )
    
    # Tracking fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_medical_records'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='updated_medical_records',
        null=True,
        blank=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    update_notes = models.TextField(
        blank=True,
        help_text="Notes about why this record was updated"
    )
    
    # Follow-up
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['patient', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.patient.patient_id} - {self.created_at.strftime('%Y-%m-%d')}"
    
    @property
    def bmi(self):
        if self.weight and self.height:
            height_in_meters = self.height / 100
            return round(self.weight / (height_in_meters ** 2), 2)
        return None
    
    @property
    def is_fever(self):
        return self.temperature and self.temperature >= 38.0
    
    @property
    def vital_signs_summary(self):
        return {
            'temperature': self.temperature,
            'blood_pressure': self.blood_pressure,
            'pulse_rate': self.pulse_rate,
            'respiratory_rate': self.respiratory_rate,
            'oxygen_saturation': self.oxygen_saturation,
            'bmi': self.bmi
        }
class Appointment(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
        ('NO_SHOW', 'No Show')
    ]

    patient = models.ForeignKey(
        'authentication.Patient',
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    doctor = models.ForeignKey(
        'authentication.Staff',
        on_delete=models.SET_NULL,
        null=True,
        related_name='doctor_appointments'
    )
    hospital = models.ForeignKey(
        'authentication.Hospital',
        on_delete=models.CASCADE,
        related_name='hospital_appointments'
    )
    appointment_datetime = models.DateTimeField()
    duration = models.DurationField(default=timezone.timedelta(minutes=30))
    appointment_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    reason = models.TextField()
    notes = models.TextField(blank=True, null=True)
    reminder_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['appointment_datetime']
        indexes = [
            models.Index(fields=['appointment_datetime']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.patient} - {self.appointment_datetime.strftime('%Y-%m-%d %H:%M')}"

    def is_upcoming(self):
        return self.appointment_datetime > timezone.now()

class LabResult(models.Model):
    RESULT_STATUS = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled')
    ]

    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='detailed_lab_results'
    )
    test_name = models.CharField(max_length=100)
    test_category = models.CharField(max_length=50)
    result_value = models.CharField(max_length=100)
    reference_range = models.CharField(max_length=100, blank=True, null=True)
    unit = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=20, choices=RESULT_STATUS, default='PENDING')
    performed_by = models.ForeignKey(
        'authentication.Staff',
        on_delete=models.SET_NULL,
        null=True,
        related_name='lab_tests_performed'
    )
    performed_date = models.DateTimeField(auto_now_add=True)
    report_file = models.FileField(
        upload_to='lab_reports/',
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-performed_date']

    def __str__(self):
        return f"{self.test_name} - {self.medical_record.patient}"

class AnalyticsData(models.Model):
    hospital = models.ForeignKey(
        'authentication.Hospital',
        on_delete=models.CASCADE,
        related_name='analytics'
    )
    date = models.DateField()
    
    # Daily Statistics
    total_appointments = models.IntegerField(default=0)
    completed_appointments = models.IntegerField(default=0)
    cancelled_appointments = models.IntegerField(default=0)
    new_patients = models.IntegerField(default=0)
    active_admissions = models.IntegerField(default=0)
    discharged_patients = models.IntegerField(default=0)
    average_stay_duration = models.DurationField(null=True, blank=True)
    
    # Department Statistics
    department_stats = models.JSONField(default=dict)
    
    # Resource Utilization
    bed_occupancy_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    class Meta:
        unique_together = ['hospital', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['hospital', '-date']),
        ]

    def __str__(self):
        return f"{self.hospital} - {self.date}"

    @classmethod
    def generate_daily_stats(cls, hospital, date):
        """
        Generate analytics data for a specific hospital and date
        """
        # This method would be implemented to calculate daily statistics
        pass