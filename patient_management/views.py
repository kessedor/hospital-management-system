from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator

# Authentication Models and Forms
from authentication.models import Patient, Staff
from authentication.forms import PatientUserForm

# Local Models
from .models import (
    Appointment,
    LabResult,
    MedicalRecord,
    Admission
)

# Local Forms
from .forms import (
    PatientForm,
    AppointmentForm,
    LabResultForm,
    MedicalRecordForm,
    AdmissionForm
)

# Existing dashboard view
@login_required
def dashboard(request):
    if not hasattr(request.user, 'hospital'):
        messages.error(request, 'Access denied. Hospital access required.')
        return redirect('login')
    return render(request, 'patient_management/patient/dashboard.html')

# Existing patient management views
@login_required
def patient_list(request):
    print("DEBUG: Patient list view accessed")
    
    if not hasattr(request.user, 'hospital'):
        print("DEBUG: No hospital access")
        messages.error(request, 'Access denied. Hospital access required.')
        return redirect('login')

    patients = Patient.objects.filter(hospital=request.user.hospital)\
        .select_related('user', 'assigned_doctor', 'assigned_doctor__user')\
        .prefetch_related('patient_admissions')
    
    print(f"DEBUG: Found {patients.count()} patients")
    patients = Patient.objects.filter(hospital=request.user.hospital)\
        .select_related('user', 'assigned_doctor', 'assigned_doctor__user')\
        .prefetch_related('patient_admissions')
    
    # ... rest of your view code
    # Get the hospital's patients with related data in one query
    patients = Patient.objects.filter(hospital=request.user.hospital)\
        .select_related('user', 'assigned_doctor', 'assigned_doctor__user')\
        .prefetch_related('patient_admissions')
    
    # Add search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        patients = patients.filter(
            Q(patient_id__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )

    # Add status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        patients = patients.filter(status=status_filter)

    # Get counts for the stats cards
    context = {
        'total_count': patients.count(),
        'admitted_count': patients.filter(status='ADMITTED').count(),
        'emergency_count': patients.filter(status='EMERGENCY').count(),
        'outpatient_count': patients.filter(status='ACTIVE').count(),
        'patients': patients,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': Patient.STATUS_CHOICES,
    }

    return render(request, 'patient_management/patient/list.html', context)

@login_required
def patient_create(request):
    print("DEBUG: Patient create view accessed")
    
    if not hasattr(request.user, 'hospital'):
        print("DEBUG: No hospital access")
        messages.error(request, 'Access denied. Hospital access required.')
        return redirect('login')
    
    if request.method == 'POST':
        print("DEBUG: POST request received")
        print(f"DEBUG: POST data: {request.POST}")
        
        user_form = PatientUserForm(request.POST)
        patient_form = PatientForm(request.POST)
        
        print(f"DEBUG: User form valid: {user_form.is_valid()}")
        print(f"DEBUG: Patient form valid: {patient_form.is_valid()}")
        
        if user_form.is_valid() and patient_form.is_valid():
            print("DEBUG: Both forms are valid")
            
            # Create User with unique username
            user = user_form.save(commit=False)
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S%f')
            user.username = f"P{timestamp}"
            user.user_type = 'PATIENT'
            user.save()
            print(f"DEBUG: User created with username: {user.username}")
            
            # Create Patient with unique patient_id
            patient = patient_form.save(commit=False)
            patient.user = user
            patient.hospital = request.user.hospital
            patient.patient_id = f"PAT{timestamp}"
            patient.save()
            print(f"DEBUG: Patient created with ID: {patient.patient_id}")
            
            messages.success(
                request,
                f'Patient {patient.user.get_full_name()} has been successfully registered with ID: {patient.patient_id}'
            )
            return redirect('patient_management:patient_detail', pk=patient.pk)
        else:
            print("DEBUG: Form errors:")
            if not user_form.is_valid():
                print(f"User form errors: {user_form.errors}")
            if not patient_form.is_valid():
                print(f"Patient form errors: {patient_form.errors}")
            messages.error(
                request,
                'Please correct the errors in the form.'
            )
    else:
        user_form = PatientUserForm()
        patient_form = PatientForm()
    
    context = {
        'user_form': user_form,
        'form': patient_form,
        'gender_choices': Patient.GENDER_CHOICES,
        'blood_group_choices': Patient.BLOOD_GROUP_CHOICES,
    }
    return render(request, 'patient_management/patient/create.html', context)

@login_required
def patient_detail(request, pk):
    if not hasattr(request.user, 'hospital'):
        messages.error(request, 'Access denied. Hospital access required.')
        return redirect('login')
    
    patient = get_object_or_404(Patient, pk=pk, hospital=request.user.hospital)
    # Add this line to fetch medical records
    medical_records = MedicalRecord.objects.filter(patient=patient).order_by('-created_at')[:5]
    
    context = {
        'patient': patient,
        'medical_records': medical_records,  # Add medical records to context
        'title': f'Patient Details - {patient.user.get_full_name()}'
    }
    return render(request, 'patient_management/patient/detail.html', context)

@login_required
def patient_update(request, pk):
    patient = get_object_or_404(Patient, pk=pk, hospital=request.user.hospital)
    
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, 'Patient information updated successfully.')
            return redirect('patient_management:patient_detail', pk=patient.pk)
    else:
        form = PatientForm(instance=patient, initial={
            'first_name': patient.user.first_name,
            'last_name': patient.user.last_name,
            'email': patient.user.email,
            'phone_number': patient.user.phone_number,
        })
    
    return render(request, 'patient_management/patient/edit.html', {
        'form': form,
        'patient': patient,
        'title': 'Edit Patient'
    })

@login_required
def patient_delete(request, pk):
    if not hasattr(request.user, 'hospital'):
        messages.error(request, 'Access denied. Hospital access required.')
        return redirect('login')
    
    patient = get_object_or_404(Patient, pk=pk, hospital=request.user.hospital)
    if request.method == 'POST':
        patient.delete()
        messages.success(request, 'Patient deleted successfully.')
        return redirect('patient_management:patient_list')
    
    return render(request, 'patient_management/patient/delete.html', {'patient': patient})

# New Appointment Management Views
@login_required
def appointment_list(request):
    if not hasattr(request.user, 'hospital'):
        messages.error(request, 'Access denied. Hospital access required.')
        return redirect('login')

    # Get filter parameters
    status = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Base queryset
    appointments = Appointment.objects.filter(hospital=request.user.hospital)
    
    # Apply filters
    if status:
        appointments = appointments.filter(status=status)
    if date_from:
        appointments = appointments.filter(appointment_datetime__date__gte=date_from)
    if date_to:
        appointments = appointments.filter(appointment_datetime__date__lte=date_to)
    
    context = {
        'upcoming_appointments': appointments.filter(
            appointment_datetime__gte=timezone.now(),
            status='SCHEDULED'
        ).select_related('patient', 'doctor'),
        'past_appointments': appointments.filter(
            appointment_datetime__lt=timezone.now()
        ).select_related('patient', 'doctor')[:10],
        'status_choices': Appointment.STATUS_CHOICES,
    }
    return render(request, 'patient_management/appointment/list.html', context)

@login_required
def appointment_create(request):
    if not hasattr(request.user, 'hospital'):
        messages.error(request, 'Access denied. Hospital access required.')
        return redirect('login')
    
    if request.method == 'POST':
        form = AppointmentForm(request.user.hospital, request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.hospital = request.user.hospital
            appointment.save()
            messages.success(request, 'Appointment scheduled successfully.')
            return redirect('patient_management:appointment_detail', pk=appointment.pk)
    else:
        form = AppointmentForm(hospital=request.user.hospital)
    
    return render(request, 'patient_management/appointment/create.html', {
        'form': form,
        'title': 'Schedule New Appointment'
    })

@login_required
def appointment_detail(request, pk):
    if not hasattr(request.user, 'hospital'):
        messages.error(request, 'Access denied. Hospital access required.')
        return redirect('login')
    
    appointment = get_object_or_404(
        Appointment, 
        pk=pk, 
        hospital=request.user.hospital
    )
    return render(request, 'patient_management/appointment/detail.html', {
        'appointment': appointment
    })

@login_required
def appointment_update(request, pk):
    if not hasattr(request.user, 'hospital'):
        messages.error(request, 'Access denied. Hospital access required.')
        return redirect('login')
    
    appointment = get_object_or_404(
        Appointment, 
        pk=pk, 
        hospital=request.user.hospital
    )
    
    if request.method == 'POST':
        form = AppointmentForm(
            request.user.hospital,
            request.POST, 
            instance=appointment
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Appointment updated successfully.')
            return redirect('patient_management:appointment_detail', pk=pk)
    else:
        form = AppointmentForm(
            hospital=request.user.hospital,
            instance=appointment
        )
    
    return render(request, 'patient_management/appointment/form.html', {
        'form': form,
        'title': 'Update Appointment',
        'appointment': appointment
    })

@login_required
def appointment_cancel(request, pk):
    if not hasattr(request.user, 'hospital'):
        messages.error(request, 'Access denied. Hospital access required.')
        return redirect('login')
    
    appointment = get_object_or_404(
        Appointment, 
        pk=pk, 
        hospital=request.user.hospital
    )
    
    if request.method == 'POST':
        appointment.status = 'CANCELLED'
        appointment.save()
        messages.success(request, 'Appointment cancelled successfully.')
        return redirect('patient_management:appointment_list')
    
    return render(request, 'patient_management/appointment/cancel.html', {
        'appointment': appointment
    })

# Lab Results Views
@login_required
def lab_result_create(request, medical_record_id):
    if not hasattr(request.user, 'hospital'):
        messages.error(request, 'Access denied. Hospital access required.')
        return redirect('login')
    
    medical_record = get_object_or_404(
        MedicalRecord, 
        pk=medical_record_id,
        hospital=request.user.hospital
    )
    
    if request.method == 'POST':
        form = LabResultForm(request.POST, request.FILES)
        if form.is_valid():
            lab_result = form.save(commit=False)
            lab_result.medical_record = medical_record
            lab_result.performed_by = request.user.staff
            lab_result.save()
            messages.success(request, 'Lab result added successfully.')
            return redirect('patient_management:medical_record_detail', pk=medical_record_id)
    else:
        form = LabResultForm()
    
    return render(request, 'patient_management/lab_result/create.html', {
        'form': form,
        'medical_record': medical_record
    })

@login_required
def lab_result_detail(request, pk):
    if not hasattr(request.user, 'hospital'):
        messages.error(request, 'Access denied. Hospital access required.')
        return redirect('login')
    
    lab_result = get_object_or_404(
        LabResult,
        pk=pk,
        medical_record__hospital=request.user.hospital
    )
    return render(request, 'patient_management/lab_result/detail.html', {
        'lab_result': lab_result
    })

# Keep existing admission and medical record views
@login_required
def admission_list(request):
    return render(request, 'patient_management/admission/list.html')


@login_required
def admission_create(request):
    if not hasattr(request.user, 'hospital'):
        messages.error(request, 'Access denied. Hospital access required.')
        return redirect('authentication:login')
    
    if request.method == 'POST':
        form = AdmissionForm(request.user.hospital, request.POST)
        if form.is_valid():
            admission = form.save(commit=False)
            admission.hospital = request.user.hospital
            admission.admission_date = timezone.now()
            admission.save()
            
            # Update patient information
            patient = admission.patient
            patient.status = 'ADMITTED' if admission.admission_type != 'EMERGENCY' else 'EMERGENCY'
            patient.admission_date = admission.admission_date
            patient.assigned_doctor = admission.primary_doctor
            patient.save()
            
            messages.success(request, 'Patient admission created successfully.')
            return redirect('patient_management:admission_list')
    else:
        initial = {}
        if request.GET.get('patient'):
            initial['patient'] = request.GET.get('patient')
        form = AdmissionForm(hospital=request.user.hospital, initial=initial)
    
    return render(request, 'patient_management/admission/create.html', {
        'form': form,
        'title': 'Create New Admission'
    })

@login_required
def admission_detail(request, pk):
    return render(request, 'patient_management/admission/detail.html')

@login_required
def medical_record_create(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id, hospital=request.user.hospital)
    
    if request.method == 'POST':
        form = MedicalRecordForm(request.user.hospital, request.POST, request.FILES)
        if form.is_valid():
            medical_record = form.save(commit=False)
            medical_record.patient = patient
            medical_record.hospital = request.user.hospital
            medical_record.created_by = request.user
            
            # If user is staff, set them as doctor
            if hasattr(request.user, 'staff_profile'):
                medical_record.doctor = request.user.staff_profile
            
            medical_record.save()
            messages.success(request, 'Medical record created successfully.')
            return redirect('patient_management:patient_detail', pk=patient.pk)
    else:
        form = MedicalRecordForm(
            hospital=request.user.hospital,
            initial={'patient': patient}
        )
        # Hide patient field as it's determined by URL
        form.fields['patient'].widget = forms.HiddenInput()
        
        # If user is staff, pre-select them as doctor
        if hasattr(request.user, 'staff_profile'):
            form.fields['doctor'].initial = request.user.staff_profile
    
    return render(request, 'patient_management/medical_record/create.html', {
        'form': form,
        'patient': patient,
        'title': 'Create Medical Record'
    })

@login_required
def medical_record_update(request, patient_id, record_id):
    patient = get_object_or_404(Patient, pk=patient_id, hospital=request.user.hospital)
    medical_record = get_object_or_404(MedicalRecord, pk=record_id, patient=patient)
    
    if request.method == 'POST':
        form = MedicalRecordForm(
            request.user.hospital, 
            request.POST, 
            request.FILES, 
            instance=medical_record
        )
        if form.is_valid():
            record = form.save(commit=False)
            record.updated_by = request.user
            record.save()
            messages.success(request, 'Medical record updated successfully.')
            return redirect('patient_management:medical_record_detail', 
                          patient_id=patient.pk, 
                          record_id=record.pk)
    else:
        form = MedicalRecordForm(
            hospital=request.user.hospital, 
            instance=medical_record
        )
    
    return render(request, 'patient_management/medical_record/update.html', {
        'form': form,
        'patient': patient,
        'medical_record': medical_record,
        'title': 'Update Medical Record'
    })

@login_required
def medical_record_detail(request, patient_id, record_id):
    if not hasattr(request.user, 'hospital'):
        messages.error(request, 'Access denied. Hospital access required.')
        return redirect('login')
    
    patient = get_object_or_404(Patient, pk=patient_id, hospital=request.user.hospital)
    record = get_object_or_404(MedicalRecord, pk=record_id, patient=patient)
    
    context = {
        'patient': patient,
        'record': record,  # Make sure to pass the record object
        'title': f'Medical Record Details - {patient.user.get_full_name()}'
    }
    return render(request, 'patient_management/medical_record/detail.html', context)


@login_required
def medical_record_list(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id, hospital=request.user.hospital)
    medical_records = patient.medical_records.all().order_by('-created_at')
    
    return render(request, 'patient_management/medical_record/list.html', {
        'patient': patient,
        'medical_records': medical_records,
        'title': 'Medical Records'
    })