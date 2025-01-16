from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from .models import User, Staff, Patient, Hospital

# Hospital Signup Form
class HospitalSignupForm(UserCreationForm):
    hospital_name = forms.CharField(max_length=100)
    address = forms.CharField(max_length=200)
    phone = forms.CharField(max_length=20)
    email = forms.EmailField()
    total_beds = forms.IntegerField(min_value=0)
    available_beds = forms.IntegerField(min_value=0)
    
    class Meta:
        model = User
        fields = ('email', 'password1', 'password2', 'hospital_name', 
                 'address', 'phone', 'total_beds', 'available_beds')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'HOSPITAL'
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            Hospital.objects.create(
                user=user,
                name=self.cleaned_data['hospital_name'],
                address=self.cleaned_data['address'],
                phone=self.cleaned_data['phone'],
                total_beds=self.cleaned_data['total_beds'],
                available_beds=self.cleaned_data['available_beds']
            )
        return user
# Patient Signup Form
class PatientSignUpForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.username = self.cleaned_data['email']  # Set username to email
        user.user_type = 'PATIENT'
        if commit:
            user.save()
        return user
# Staff Forms
class StaffUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number']

class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = [
            'employee_id',
            'role',
            'department',
            'specialization',
            'qualification',
            'experience_years',
            'status',
            'joining_date',
            'emergency_contact',
            'address'
        ]
        widgets = {
            'joining_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class StaffScheduleForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = ['schedule']
        widgets = {
            'schedule': forms.Textarea(attrs={
                'rows': 4, 
                'placeholder': '{"Monday": "9:00-17:00", "Tuesday": "9:00-17:00"}'
            })
        }

    def clean_schedule(self):
        import json
        schedule = self.cleaned_data.get('schedule')
        try:
            if isinstance(schedule, str):
                return json.loads(schedule)
            return schedule
        except json.JSONDecodeError:
            raise forms.ValidationError("Please enter a valid JSON schedule")

# Patient Forms
class PatientUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'required': True}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
        }

class PatientForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True
    )

    class Meta:
        model = Patient
        fields = [
            'date_of_birth',
            'gender',
            'blood_group',
            'address',
            'emergency_contact',
            'emergency_contact_relation',
            'medical_history',
            'current_medications',
            'allergies',
            'notes'
        ]
        widgets = {
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'blood_group': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_relation': forms.TextInput(attrs={'class': 'form-control'}),
            'medical_history': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'current_medications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob > timezone.now().date():
            raise forms.ValidationError("Date of birth cannot be in the future")
        return dob

    def clean_emergency_contact(self):
        contact = self.cleaned_data.get('emergency_contact')
        if contact and not contact.isdigit():
            raise forms.ValidationError("Emergency contact should contain only numbers")
        return contact