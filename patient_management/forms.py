from django import forms
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from authentication.models import Staff, User
from .models import (
    Admission,
    Appointment,
    LabResult,
    MedicalRecord,
    Patient
)

class PatientForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField(required=False)
    phone_number = forms.CharField(max_length=15, required=False)
    
    class Meta:
        model = Patient
        fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'date_of_birth', 'gender', 'blood_group',
            'address', 'emergency_contact', 'emergency_contact_relation',
            'medical_history', 'allergies', 'notes'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 2}),
            'medical_history': forms.Textarea(attrs={'rows': 3}),
            'allergies': forms.Textarea(attrs={'rows': 2}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })
        # Add choices for gender and blood group
        self.fields['gender'].widget = forms.Select(choices=Patient.GENDER_CHOICES)
        self.fields['blood_group'].widget = forms.Select(choices=Patient.BLOOD_GROUP_CHOICES)
        
        # If instance exists, populate user fields
        if self.instance and self.instance.pk:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            self.fields['phone_number'].initial = self.instance.user.phone_number

    def is_valid(self):
        valid = super().is_valid()
        if not valid:
            print("DEBUG: PatientForm validation errors:", self.errors)
        return valid

    def save(self, commit=True):
        if not self.instance.pk:  # Only for new patients
            # Generate unique username using timestamp
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S%f')
            email = self.cleaned_data.get('email')
            username = f"PAT_{timestamp}"

            # Create user first
            user = User.objects.create(
                username=username,
                email=email,
                first_name=self.cleaned_data.get('first_name'),
                last_name=self.cleaned_data.get('last_name'),
                user_type='PATIENT'
            )

            # Set the user for the patient
            self.instance.user = user

        return super().save(commit)

class AdmissionForm(forms.ModelForm):
    class Meta:
        model = Admission
        fields = [
            'patient', 'admission_type', 'ward', 'bed_number',
            'primary_doctor', 'chief_complaint', 'notes'
        ]
        widgets = {
            'chief_complaint': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, hospital, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter patients and doctors by hospital
        self.fields['patient'].queryset = Patient.objects.filter(hospital=hospital)
        self.fields['primary_doctor'].queryset = Staff.objects.filter(
            hospital=hospital,
            role='DOCTOR',
            status='ACTIVE'
        )
        
        # Add Bootstrap classes
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })



class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = [
            'patient',
            'doctor',
            'temperature',
            'blood_pressure',
            'pulse_rate',
            'respiratory_rate',
            'weight',
            'height',
            'oxygen_saturation',
            'symptoms',
            'diagnosis',
            'treatment',
            'prescription',
            'notes',
            'lab_results',
            'attachments',
            'follow_up_date',
            'follow_up_notes',
            'update_notes'
        ]
        widgets = {
            'symptoms': forms.Textarea(attrs={'rows': 3}),
            'diagnosis': forms.Textarea(attrs={'rows': 3}),
            'treatment': forms.Textarea(attrs={'rows': 3}),
            'prescription': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'follow_up_notes': forms.Textarea(attrs={'rows': 3}),
            'update_notes': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Reason for updating this record (if applicable)'
            }),
            'follow_up_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, hospital, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter doctors by hospital
        self.fields['doctor'].queryset = Staff.objects.filter(hospital=hospital)
        
        # Add Bootstrap classes
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

        # Make update_notes optional
        self.fields['update_notes'].required = False
        
        # Add help texts
        self.fields['blood_pressure'].help_text = "Format: 120/80"
        self.fields['temperature'].help_text = "In Celsius"
        self.fields['weight'].help_text = "In kilograms"
        self.fields['height'].help_text = "In centimeters"
        self.fields['oxygen_saturation'].help_text = "In percentage"

    def clean(self):
        cleaned_data = super().clean()
        
        # Validate vital signs
        temperature = cleaned_data.get('temperature')
        if temperature and (temperature < 35 or temperature > 42):
            self.add_error('temperature', "Temperature must be between 35°C and 42°C")

        blood_pressure = cleaned_data.get('blood_pressure')
        if blood_pressure:
            try:
                systolic, diastolic = map(int, blood_pressure.split('/'))
                if systolic < 70 or systolic > 200 or diastolic < 40 or diastolic > 120:
                    self.add_error('blood_pressure', "Blood pressure values are out of normal range")
            except ValueError:
                self.add_error('blood_pressure', "Blood pressure must be in format '120/80'")

        pulse_rate = cleaned_data.get('pulse_rate')
        if pulse_rate and (pulse_rate < 40 or pulse_rate > 200):
            self.add_error('pulse_rate', "Pulse rate must be between 40 and 200")

        oxygen_saturation = cleaned_data.get('oxygen_saturation')
        if oxygen_saturation and (oxygen_saturation < 0 or oxygen_saturation > 100):
            self.add_error('oxygen_saturation', "Oxygen saturation must be between 0 and 100")

        return cleaned_data

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [
            'patient', 'doctor', 'appointment_datetime',
            'duration', 'appointment_type', 'reason', 'notes'
        ]
        widgets = {
            'appointment_datetime': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'reason': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
        }

    def __init__(self, hospital=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hospital:
            self.fields['patient'].queryset = Patient.objects.filter(hospital=hospital)
            self.fields['doctor'].queryset = Staff.objects.filter(
                hospital=hospital,
                role='DOCTOR',
                status='ACTIVE'
            )
        
        # Add Bootstrap classes
        for field in self.fields:
            if 'class' not in self.fields[field].widget.attrs:
                self.fields[field].widget.attrs['class'] = 'form-control'

    def clean_appointment_datetime(self):
        datetime = self.cleaned_data['appointment_datetime']
        if datetime < timezone.now():
            raise forms.ValidationError("Appointment cannot be scheduled in the past.")
        return datetime

class LabResultForm(forms.ModelForm):
    class Meta:
        model = LabResult
        fields = [
            'test_name', 'test_category', 'result_value',
            'reference_range', 'unit', 'notes', 'report_file'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'report_file': forms.FileInput(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if 'class' not in self.fields[field].widget.attrs:
                self.fields[field].widget.attrs['class'] = 'form-control'