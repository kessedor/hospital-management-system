from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import datetime
from datetime import date
from django.utils import timezone
from dateutil.relativedelta import relativedelta

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('HOSPITAL', 'Hospital'),
        ('STAFF', 'Staff'),
        ('PATIENT', 'Patient'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='PATIENT')
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.user_type})"

class Hospital(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=50, unique=True)
    address = models.TextField()
    primary_phone = models.CharField(max_length=15)
    phone_number = models.CharField(max_length=20, default="Not Available")
    email = models.EmailField(default="hospital@example.com")
    total_beds = models.IntegerField(default=0)
    available_beds = models.IntegerField(default=0)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    emergency_status = models.CharField(
        max_length=10,
        choices=(('OPEN', 'Open'), ('CLOSED', 'Closed')),
        default='OPEN'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.phone_number or self.phone_number == "Not Available":
            self.phone_number = self.primary_phone
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Hospitals"

    def doctor_count(self):
        """Returns the count of doctors in the hospital"""
        return self.staff_members.filter(role='DOCTOR').count()


class Department(models.Model):
    hospital = models.ForeignKey('Hospital', on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.hospital.name}"

class Staff(models.Model):
    ROLE_CHOICES = (
        ('DOCTOR', 'Doctor'),
        ('NURSE', 'Nurse'),
        ('ADMIN', 'Administrative Staff'),
        ('LAB', 'Laboratory Technician'),
        ('PHARM', 'Pharmacist'),
        ('OTHER', 'Other'),
    )

    DEPARTMENT_CHOICES = (
        ('EMERGENCY', 'Emergency'),
        ('CARDIOLOGY', 'Cardiology'),
        ('PEDIATRICS', 'Pediatrics'),
        ('NEUROLOGY', 'Neurology'),
        ('ORTHOPEDICS', 'Orthopedics'),
        ('ONCOLOGY', 'Oncology'),
        ('GENERAL', 'General Medicine'),
        ('ADMIN', 'Administration'),
        ('OTHER', 'Other'),
    )

    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('ON_LEAVE', 'On Leave'),
        ('INACTIVE', 'Inactive'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='staff_members')
    employee_id = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES)
    specialization = models.CharField(max_length=100, blank=True)
    qualification = models.CharField(max_length=100)
    experience_years = models.IntegerField(default=0)
    schedule = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    joining_date = models.DateField(null=True, blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role} ({self.employee_id})"

    class Meta:
        verbose_name_plural = "Staff Members"
        ordering = ['role', 'user__first_name']

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('ADMITTED', 'Admitted'),
        ('EMERGENCY', 'Emergency'),
        ('DISCHARGED', 'Discharged'),
        ('INACTIVE', 'Inactive'),
    )
    
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )

    BLOOD_GROUP_CHOICES = (
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='patients', null=True, blank=True)
    patient_id = models.CharField(max_length=20, unique=True)
    primary_phone = models.CharField(max_length=15, blank=True, default='')
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES)
    address = models.TextField()
    emergency_contact = models.CharField(max_length=15)
    emergency_contact_relation = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    admission_date = models.DateTimeField(null=True, blank=True)
    discharge_date = models.DateTimeField(null=True, blank=True)
    assigned_doctor = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name='patients')
    diagnosis = models.TextField(blank=True)
    medical_history = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.patient_id:
            # Generate patient ID: P + 6-digit user ID
            self.patient_id = f"P{str(self.user.id).zfill(6)}"
        
        # Ensure primary phone is set
        if not self.primary_phone:
            self.primary_phone = self.user.username
            
        super().save(*args, **kwargs)

    @property
    def age(self):
        today = date.today()
        if self.date_of_birth:
            age = today.year - self.date_of_birth.year
            # Adjust age if birthday hasn't occurred this year
            if today.month < self.date_of_birth.month or (
                today.month == self.date_of_birth.month and 
                today.day < self.date_of_birth.day
            ):
                age -= 1
            return age
        return None

    @property
    def latest_medical_record(self):
        return self.medical_records.order_by('-created_at').first()

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.patient_id})"

    class Meta:
        verbose_name_plural = "Patients"
        ordering = ['-created_at']

class InventoryCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='inventory_categories')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Inventory Categories"
        ordering = ['name']
        unique_together = ['hospital', 'name']

    def __str__(self):
        return f"{self.name} - {self.hospital.name}"

class InventoryItem(models.Model):
    CRITICALITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    )

    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='inventory_items')
    category = models.ForeignKey(InventoryCategory, on_delete=models.SET_NULL, null=True, related_name='items')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    quantity = models.IntegerField(default=0)
    unit = models.CharField(max_length=50)
    minimum_stock = models.IntegerField(default=10)
    criticality = models.CharField(max_length=10, choices=CRITICALITY_CHOICES, default='MEDIUM')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    supplier_info = models.TextField(blank=True)
    storage_location = models.CharField(max_length=100, blank=True)
    last_ordered_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def needs_restock(self):
        """Check if item needs restocking based on minimum stock level"""
        return self.quantity <= self.minimum_stock

    @property
    def is_expired(self):
        """Check if item is expired"""
        if self.expiry_date:
            return self.expiry_date <= timezone.now().date()
        return False

    class Meta:
        verbose_name_plural = "Inventory Items"
        ordering = ['category', 'name']
        unique_together = ['hospital', 'name']

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"

class InventoryTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJUST', 'Adjustment'),
    )

    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()
    previous_quantity = models.IntegerField()
    new_quantity = models.IntegerField()
    transaction_date = models.DateTimeField(auto_now_add=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    reference_number = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ['-transaction_date']

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.item.name} ({self.quantity} {self.item.unit})"

    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = f"TXN-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        super().save(*args, **kwargs)