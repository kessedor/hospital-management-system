from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from authentication.models import Hospital, Department, Patient
from .models import Appointment
from datetime import datetime, timedelta, date

def home(request):
    """Home page view - accessible to all users"""
    if request.user.is_authenticated and request.user.user_type == 'HOSPITAL':
        return redirect('authentication:hospital_dashboard')
    return render(request, 'home/home.html')
@login_required
def hospital_search(request):
    """Hospital search view with dashboard features for patients"""
    query = request.GET.get('q', '')
    location = request.GET.get('location', '')
    
    hospitals = Hospital.objects.all().order_by('name')
    
    if query:
        hospitals = hospitals.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )
    
    if location:
        hospitals = hospitals.filter(
            Q(address__icontains=location) |
            Q(city__icontains=location) |
            Q(state__icontains=location)
        )
    
    # Dashboard data for authenticated patients
    dashboard_data = {}
    if request.user.is_authenticated and hasattr(request.user, 'patient'):
        patient = request.user.patient
        upcoming_appointments = Appointment.objects.filter(
            patient=patient,
            appointment_date__gte=timezone.now().date(),
            status='CONFIRMED'
        ).order_by('appointment_date')
        
        dashboard_data = {
            'upcoming_appointments_count': upcoming_appointments.count(),
            'next_appointment': upcoming_appointments.first(),
            'recent_visits_count': Appointment.objects.filter(
                patient=patient,
                status='COMPLETED'
            ).count(),
        }
    
    hospitals = list(hospitals)
    paginator = Paginator(hospitals, 9)
    page = request.GET.get('page')
    hospitals = paginator.get_page(page)
    
    context = {
        'hospitals': hospitals,
        'query': query,
        'location': location,
        **dashboard_data  # Add dashboard data to context
    }
    
    return render(request, 'home/hospital_search.html', context)

def hospital_detail(request, hospital_id):
    """Hospital detail view"""
    hospital = get_object_or_404(Hospital, id=hospital_id)
    
    if request.user.is_authenticated and request.user.user_type == 'HOSPITAL':
        if request.user.hospital.id == hospital_id:
            return redirect('authentication:hospital_dashboard')
        messages.warning(request, "You can only view your own hospital dashboard.")
        return redirect('authentication:hospital_dashboard')
    
    if not request.user.is_authenticated:
        messages.warning(request, "Please login as a patient to book appointments.")
        return redirect('authentication:login')
    
    return redirect('home:book_appointment', hospital_id=hospital_id)

@login_required
def my_profile(request):
    """View for displaying and editing patient profile"""
    try:
        patient = request.user.patient_profile  # Using patient_profile to match your model
        
        if request.method == 'POST':
            # Handle profile updates
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone_number')
            address = request.POST.get('address')
            
            # Update user info
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.email = email
            request.user.save()
            
            # Update patient info
            patient.primary_phone = phone
            patient.address = address
            patient.save()
            
            messages.success(request, "Profile updated successfully!")
            return redirect('home:my_profile')
        
        context = {
            'patient': patient,
            'user': request.user
        }
        return render(request, 'home/my_profile.html', context)
        
    except Exception as e:
        print(f"Error in my_profile view: {str(e)}")
        messages.error(request, "An error occurred while loading your profile.")
        return redirect('home:hospital_search')

@login_required
def book_appointment(request, hospital_id):
    """Handle appointment booking"""
    print("=== Book Appointment Debug ===")
    print(f"User: {request.user.username}")
    print(f"Hospital ID: {hospital_id}")
    
    try:
        hospital = get_object_or_404(Hospital, id=hospital_id)
        departments = hospital.departments.all()
        
        print(f"Found hospital: {hospital.name}")
        print(f"Found {departments.count()} departments")
        
        if request.method == 'POST':
            department_id = request.POST.get('department')
            appointment_date = request.POST.get('appointment_date')
            time_slot = request.POST.get('time_slot')
            reason = request.POST.get('reason')
            
            try:
                # Check for existing appointments in the same time slot
                existing_appointments = Appointment.objects.filter(
                    department_id=department_id,
                    appointment_date=appointment_date,
                    time_slot=time_slot
                ).count()
                
                MAX_APPOINTMENTS_PER_SLOT = 3  # You can adjust this number
                if existing_appointments >= MAX_APPOINTMENTS_PER_SLOT:
                    messages.error(request, "Sorry, this time slot is fully booked. Please select another time.")
                    return redirect('home:book_appointment', hospital_id=hospital_id)
                
                # Create the appointment
                appointment = Appointment.objects.create(
                    patient=request.user.patient_profile,
                    hospital=hospital,
                    department_id=department_id,
                    appointment_date=appointment_date,
                    time_slot=time_slot,
                    reason=reason,
                    status='PENDING'
                )
                
                # Send email notifications
                from .utils import send_appointment_confirmation_email
                send_appointment_confirmation_email(appointment)
                
                messages.success(request, 
                    "Your appointment has been booked successfully! "
                    "You will receive a confirmation email shortly."
                )
                return redirect('home:appointment_confirmation', appointment_id=appointment.id)
                
            except Exception as e:
                print(f"Error creating appointment: {str(e)}")
                messages.error(request, "Error booking appointment. Please try again.")
                return redirect('home:book_appointment', hospital_id=hospital_id)
        
        # Debug prints for departments
        print("\nDebug - Departments:")
        for dept in departments:
            print(f"- {dept.name} (ID: {dept.id})")
        
        if request.user.user_type != 'PATIENT':
            print("User is not a patient type")
            messages.error(request, "Only patients can book appointments.")
            return redirect('home:hospital_search')
        
        if not hasattr(request.user, 'patient_profile'):
            try:
                patient = Patient.objects.create(
                    user=request.user,
                    hospital=hospital,
                    patient_id=f"P{request.user.id:06d}",
                    primary_phone=request.user.username,
                    date_of_birth=date(2000, 1, 1),
                    gender='O',
                    blood_group='O+',
                    address="Address pending",
                    emergency_contact="Pending",
                    emergency_contact_relation="Pending",
                    status='ACTIVE'
                )
                print(f"Created new patient profile: {patient.patient_id}")
            except Exception as e:
                print(f"Error creating patient profile: {str(e)}")
                messages.error(request, "Error creating patient profile. Please contact support.")
                return redirect('home:hospital_search')
        
        print("User is a patient, proceeding...")
        
        if departments.count() == 0:
            print("No departments found, creating default departments")
            default_departments = [
                {"name": "General Medicine", "description": "General healthcare services"},
                {"name": "Pediatrics", "description": "Children's healthcare"},
                {"name": "Cardiology", "description": "Heart and cardiovascular care"},
                {"name": "Orthopedics", "description": "Bone and joint care"}
            ]
            for dept in default_departments:
                Department.objects.create(hospital=hospital, **dept)
            departments = hospital.departments.all()
            print(f"Created {departments.count()} default departments")
        
        # Get next 7 days
        today = datetime.now()
        available_dates = [(today + timedelta(days=x)).date() for x in range(7)]
        
        # Create time slots
        time_slots = [
            {'value': '0900', 'label': '9:00 AM'},
            {'value': '1000', 'label': '10:00 AM'},
            {'value': '1100', 'label': '11:00 AM'},
            {'value': '1400', 'label': '2:00 PM'},
            {'value': '1500', 'label': '3:00 PM'},
            {'value': '1600', 'label': '4:00 PM'},
        ]
        
        # Debug prints for dates
        print("\nDebug - Available Dates:")
        for date in available_dates:
            print(f"- {date.strftime('%Y-%m-%d')}")
        
        context = {
            'hospital': hospital,
            'departments': departments,
            'available_dates': available_dates,
            'available_time_slots': time_slots,
        }
        
        print("Rendering booking template...")
        return render(request, 'home/book_appointment.html', context)
        
    except Exception as e:
        print(f"Error in book_appointment: {str(e)}")
        messages.error(request, "An error occurred while loading the booking form. Please try again.")
        return redirect('home:hospital_search')
@login_required
def appointment_confirmation(request, appointment_id):
    """Display appointment confirmation details"""
    try:
        appointment = get_object_or_404(
            Appointment, 
            id=appointment_id,
            patient__user=request.user
        )
        
        context = {
            'appointment': appointment,
            'hospital': appointment.hospital,
            'department': appointment.department,
        }
        
        return render(request, 'home/appointment_confirmation.html', context)
        
    except Exception as e:
        print(f"Error displaying appointment confirmation: {str(e)}")
        messages.error(request, "Error displaying appointment confirmation.")
        return redirect('home:hospital_search')

@login_required
def my_appointments(request):
    """View for displaying patient's appointments"""
    try:
        # Get all appointments for the current patient
        appointments = Appointment.objects.filter(
            patient=request.user.patient_profile  # Note: using patient_profile instead of patient
        ).order_by('-appointment_date')
        
        context = {
            'appointments': appointments,
            'today': datetime.now().date()  # Add today's date for comparison
        }
        return render(request, 'home/my_appointments.html', context)
        
    except Exception as e:
        print(f"Error in my_appointments view: {str(e)}")
        messages.error(request, "An error occurred while loading your appointments.")
        return redirect('home:hospital_search')
@login_required
def cancel_appointment(request, appointment_id):
    try:
        appointment = get_object_or_404(
            Appointment, 
            id=appointment_id,
            patient__user=request.user
        )
        
        appointment.status = 'CANCELLED'
        appointment.save()
        
        messages.success(request, "Appointment cancelled successfully.")
        return redirect('home:my_appointments')
        
    except Exception as e:
        print(f"Error cancelling appointment: {str(e)}")
        messages.error(request, "Error cancelling appointment.")
        return redirect('home:my_appointments')