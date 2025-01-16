from .models import Schedule, LeaveRequest
from datetime import datetime
from django import forms
from django.contrib.auth import get_user_model
from authentication.models import User, Hospital, Staff
from django.core.exceptions import ValidationError
import random
import string

class HospitalRegistrationForm(forms.ModelForm):
    class Meta:
        model = Hospital
        fields = ['name', 'registration_number', 'address', 'primary_phone', 'total_beds', 'available_beds']

    user_email = forms.EmailField(required=True)
    user_password = forms.CharField(widget=forms.PasswordInput, required=True)

    def save(self, commit=True):
        user_email = self.cleaned_data.pop('user_email')
        user_password = self.cleaned_data.pop('user_password')
        user = User.objects.create_user(
            username=user_email,
            email=user_email,
            password=user_password,
            user_type='HOSPITAL'
        )
        hospital = super().save(commit=False)
        hospital.user = user
        if commit:
            hospital.save()
        return hospital

class StaffCreationForm(forms.ModelForm):
    # User account fields
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=15)
    
    class Meta:
        model = Staff
        fields = [
            'first_name', 'last_name', 'email', 'phone_number',  # User fields
            'employee_id', 'role', 'department',
            'qualification', 'experience_years',
            'emergency_contact', 'address'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('A user with this email already exists.')
        return email

    def generate_random_password(self):
        """Generate a random password"""
        chars = string.ascii_letters + string.digits + string.punctuation
        return ''.join(random.choice(chars) for _ in range(12))

    def save(self, commit=True, hospital=None):
        # Create User instance
        user = User.objects.create_user(
            username=self.cleaned_data['email'],
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            phone_number=self.cleaned_data['phone_number'],
            password=self.generate_random_password(),  # Using our custom method
            user_type='STAFF'
        )
        
        # Create Staff instance
        staff = super().save(commit=False)
        staff.user = user
        staff.hospital = hospital  # Set the hospital
        
        if commit:
            staff.save()
        
        return staff

class StaffUpdateForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = [
            'role', 'department',
            'qualification', 'experience_years',
            'status', 'emergency_contact', 'address'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make certain fields optional for updates
        for field in self.fields:
            self.fields[field].required = False
class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['staff', 'date', 'shift']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'shift': forms.Select(choices=Schedule.SHIFT_CHOICES)
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].widget.attrs.update({'class': 'form-control'})
        self.fields['shift'].widget.attrs.update({'class': 'form-control'})
        self.fields['staff'].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        staff = cleaned_data.get('staff')
        date = cleaned_data.get('date')
        shift = cleaned_data.get('shift')

        if staff and date and shift:
            # Check for existing schedule
            if Schedule.objects.filter(
                staff=staff,
                date=date,
                shift=shift
            ).exists():
                raise ValidationError('This staff member is already scheduled for this shift.')

            # Check for leave requests
            if LeaveRequest.objects.filter(
                staff=staff,
                start_date__lte=date,
                end_date__gte=date,
                status='APPROVED'
            ).exists():
                raise ValidationError('This staff member is on approved leave for this date.')

        return cleaned_data

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 3})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError('End date must be after start date.')

            if start_date < datetime.now().date():
                raise ValidationError('Start date cannot be in the past.')

        return cleaned_data