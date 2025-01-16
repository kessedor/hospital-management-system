from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def send_appointment_confirmation_email(appointment):
    """Send confirmation email to patient and notification to hospital"""
    try:
        # Get patient details
        patient = appointment.patient
        patient_name = patient.user.get_full_name()
        if not patient_name.strip():
            patient_name = patient.user.username

        # Ensure patient has an ID and phone number
        if not patient.patient_id:
            patient.save()  # This will trigger the auto-generation
        
        if not patient.primary_phone:
            patient.primary_phone = patient.user.username
            patient.save()

        # Ensure hospital has a phone number
        if appointment.hospital.phone_number == "Not Available":
            appointment.hospital.phone_number = appointment.hospital.primary_phone
            appointment.hospital.save()

        # Email to patient
        patient_subject = f'Appointment Confirmation - {appointment.hospital.name}'
        patient_context = {
            'patient_name': patient_name,
            'hospital_name': appointment.hospital.name,
            'department_name': appointment.department.name,
            'appointment_date': appointment.appointment_date,
            'appointment_time': appointment.get_time_slot_display(),
            'hospital_address': appointment.hospital.address,
            'hospital_phone': appointment.hospital.phone_number or appointment.hospital.primary_phone,
        }
        
        patient_message = render_to_string('emails/appointment_confirmation.html', patient_context)
        
        send_mail(
            subject=patient_subject,
            message=patient_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[appointment.patient.user.email],
            fail_silently=False,
            html_message=patient_message
        )
        
        # Email to hospital
        hospital_subject = f'New Appointment Request - {patient_name}'
        hospital_context = {
            'patient_name': patient_name,
            'patient_id': patient.patient_id,
            'department_name': appointment.department.name,
            'appointment_date': appointment.appointment_date,
            'appointment_time': appointment.get_time_slot_display(),
            'reason': appointment.reason,
            'patient_email': patient.user.email,
            'patient_phone': patient.primary_phone or "Not provided",
        }
        
        hospital_message = render_to_string('emails/hospital_appointment_notification.html', hospital_context)
        
        send_mail(
            subject=hospital_subject,
            message=hospital_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[appointment.hospital.email],
            fail_silently=False,
            html_message=hospital_message
        )
        
        print(f"Appointment confirmation emails sent successfully for appointment ID: {appointment.id}")
        return True
        
    except Exception as e:
        print(f"Error sending appointment confirmation emails: {str(e)}")
        return False
def get_available_time_slots(department, date):
    """Get available time slots for a given department and date"""
    from .models import Appointment
    
    all_time_slots = dict(Appointment.TIME_SLOTS)
    booked_slots = Appointment.objects.filter(
        department=department,
        appointment_date=date
    ).values_list('time_slot', flat=True)
    
    available_slots = []
    for slot_value, slot_label in all_time_slots.items():
        if slot_value not in booked_slots:
            available_slots.append({
                'value': slot_value,
                'label': slot_label
            })
    
    return available_slots