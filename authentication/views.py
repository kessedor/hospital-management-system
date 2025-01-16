from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from django.template.context_processors import csrf
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.text import slugify
from django.utils import timezone
from django.urls import reverse
from django.http import JsonResponse
from django.db.models import Sum, Count, F, Q
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from django.conf import settings
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from django.contrib.auth.tokens import default_token_generator
import random
import string
import uuid
import json
import base64
from email.mime.text import MIMEText
import logging
logger = logging.getLogger(__name__)


# Google OAuth2 imports
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# Local imports
from home.models import Appointment
from .models import (
    Hospital, Staff, Patient,
    InventoryItem, InventoryCategory,
    InventoryTransaction, User
)
from .utilities import is_hospital_staff
from .forms import PatientSignUpForm, HospitalSignupForm
from .tokens import account_activation_token
from .gmail_settings import get_flow, SCOPES

# Utility Functions
def is_hospital_staff(user):
    if not user.is_authenticated:
        return False
    try:
        return hasattr(user, 'hospital') and user.hospital is not None
    except Hospital.DoesNotExist:
        return False

# Authentication Views
@ensure_csrf_cookie
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('username')  # Form still sends as 'username'
        password = request.POST.get('password')
        
        try:
            # First try to get a hospital user
            users = User.objects.filter(email=email)
            user = None
            
            # Prioritize hospital user if exists
            for u in users:
                if hasattr(u, 'hospital'):
                    user = u
                    break
            
            # If no hospital user found, take the first user
            if not user and users.exists():
                user = users.first()
            
            if user:
                # Authenticate with username and password
                auth_user = authenticate(request, username=user.username, password=password)
                
                if auth_user is not None:
                    login(request, auth_user)
                    # Set session expiry to 24 hours
                    request.session.set_expiry(86400)
                    
                    if hasattr(auth_user, 'hospital'):
                        return redirect('authentication:hospital_dashboard')
                    else:
                        return redirect('home:hospital_search')
                else:
                    messages.error(request, 'Invalid email or password.')
            else:
                messages.error(request, 'Invalid email or password.')
                
        except Exception as e:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'authentication/login.html')

def logout_view(request):
    logout(request)
    return redirect('authentication:login')

def activate_account(request, uidb64, token):
    """Activate a user's account and create appropriate profile."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()

        # Create profile based on user type
        if user.user_type == 'HOSPITAL':
            # Existing hospital logic remains unchanged
            if not hasattr(user, 'hospital'):
                import uuid
                reg_number = f"NHRS-{str(uuid.uuid4())[:8].upper()}"
                while Hospital.objects.filter(registration_number=reg_number).exists():
                    reg_number = f"NHRS-{str(uuid.uuid4())[:8].upper()}"
                
                hospital_name = user.username.replace('-', ' ').title()
                Hospital.objects.create(
                    user=user,
                    name=hospital_name,
                    address="",  # They can update this later
                    phone_number="",  # They can update this later
                    registration_number=reg_number
                )
        
        elif user.user_type == 'PATIENT':
            # New patient logic
            if not hasattr(user, 'patient_profile'):
                patient_id = f"P{str(user.id).zfill(6)}"
                Patient.objects.create(
                    user=user,
                    patient_id=patient_id,
                    primary_phone=user.phone_number or '',
                    # Other fields will be filled later by the patient
                )

        messages.success(request, 'Your account has been activated successfully. You can now log in.')
        return redirect('authentication:login')
    else:
        messages.error(request, 'The activation link is invalid or has expired.')
        return redirect('authentication:login')

def hospital_signup_view(request):
    if request.method == 'POST':
        form = HospitalSignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            base_username = slugify(form.cleaned_data['hospital_name'])
            username = f"{base_username}-{str(uuid.uuid4())[:8]}"
            user.username = username
            user.is_active = False
            user.save()
            
            # Store registration data in session for after OAuth
            request.session['pending_registration'] = {
                'user_id': user.pk,
                'email': user.email,
                'activation_link': request.build_absolute_uri(
                    reverse('authentication:activate', kwargs={
                        'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
                        'token': account_activation_token.make_token(user)
                    })
                )
            }
            
            # Redirect to Gmail OAuth2 flow
            return redirect('authentication:gmail_auth_init')
    else:
        form = HospitalSignupForm()
    return render(request, 'authentication/hospital_signup.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.user_type == 'HOSPITAL')  # Only allow hospital users
def hospital_dashboard(request):
    try:
        hospital = request.user.hospital
        occupancy_rate = 0
        if hospital.total_beds > 0:
            occupancy_rate = ((hospital.total_beds - hospital.available_beds) / hospital.total_beds) * 100
            
        context = {
            'hospital': hospital,
            'occupancy_rate': occupancy_rate
        }
        return render(request, 'authentication/hospital_dashboard.html', context)
    except Exception as e:
        messages.error(request, f'Error loading dashboard: {str(e)}')
        return redirect('authentication:login')
@login_required
def profile_view(request):
    return render(request, 'authentication/profile.html')

@login_required
def edit_profile_view(request):
    return render(request, 'authentication/edit_profile.html')

@login_required
def change_password_view(request):
    return render(request, 'authentication/change_password.html')

@login_required
@user_passes_test(is_hospital_staff)
def inventory_management(request):
    try:
        hospital = get_object_or_404(Hospital, user=request.user)
        items = InventoryItem.objects.filter(hospital=hospital).select_related('category')
        categories = InventoryCategory.objects.filter(hospital=hospital, is_active=True)
        low_stock_items = items.filter(quantity__lte=F('minimum_stock'))
        expired_items = items.filter(expiry_date__lte=timezone.now().date())
        recent_transactions = InventoryTransaction.objects.filter(
            item__hospital=hospital
        ).select_related('item', 'performed_by').order_by('-transaction_date')[:10]
        
        context = {
            'items': items,
            'categories': categories,
            'total_items': items.count(),
            'low_stock': low_stock_items.count(),
            'expired': expired_items.count(),
            'recent_transactions': recent_transactions,
            'categories_count': categories.count(),
            'page': 'inventory'
        }
        return render(request, 'authentication/inventory_management.html', context)
    except Exception as e:
        messages.error(request, f'Error loading inventory: {str(e)}')
        return redirect('authentication:hospital_dashboard')
@login_required
@user_passes_test(is_hospital_staff)
def add_inventory_item(request):
    if request.method == 'POST':
        try:
            hospital = get_object_or_404(Hospital, user=request.user)
            
            # Create new inventory item
            item = InventoryItem.objects.create(
                hospital=hospital,
                name=request.POST.get('name'),
                category_id=request.POST.get('category'),
                quantity=int(request.POST.get('quantity', 0)),
                unit=request.POST.get('unit'),
                minimum_stock=int(request.POST.get('minimum_stock', 0)),
                unit_price=float(request.POST.get('unit_price', 0)),
                description=request.POST.get('description', ''),
                expiry_date=request.POST.get('expiry_date')
            )
            
            # Create initial stock transaction
            InventoryTransaction.objects.create(
                item=item,
                transaction_type='IN',
                quantity=item.quantity,
                performed_by=request.user,
                notes='Initial stock entry'
            )
            
            messages.success(request, 'Inventory item added successfully')
            return JsonResponse({'status': 'success', 'message': 'Item added successfully'})
            
        except Exception as e:
            messages.error(request, f'Error adding inventory item: {str(e)}')
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@login_required
@user_passes_test(is_hospital_staff)
def edit_inventory_item(request, item_id):
    try:
        item = get_object_or_404(InventoryItem, id=item_id, hospital__user=request.user)
        
        if request.method == 'POST':
            item.name = request.POST.get('name')
            item.category_id = request.POST.get('category')
            item.unit = request.POST.get('unit')
            item.minimum_stock = int(request.POST.get('minimum_stock', 0))
            item.unit_price = float(request.POST.get('unit_price', 0))
            item.description = request.POST.get('description', '')
            item.expiry_date = request.POST.get('expiry_date')
            item.save()
            
            messages.success(request, 'Inventory item updated successfully')
            return JsonResponse({'status': 'success', 'message': 'Item updated successfully'})
            
        context = {
            'item': item,
            'categories': InventoryCategory.objects.filter(hospital=item.hospital, is_active=True)
        }
        return render(request, 'authentication/edit_inventory_item.html', context)
        
    except Exception as e:
        messages.error(request, f'Error updating inventory item: {str(e)}')
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@user_passes_test(is_hospital_staff)
def delete_inventory_item(request, item_id):
    if request.method == 'POST':
        try:
            item = get_object_or_404(InventoryItem, id=item_id, hospital__user=request.user)
            item.delete()
            messages.success(request, 'Inventory item deleted successfully')
            return JsonResponse({'status': 'success', 'message': 'Item deleted successfully'})
        except Exception as e:
            messages.error(request, f'Error deleting inventory item: {str(e)}')
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@login_required
@user_passes_test(is_hospital_staff)
def update_inventory_stock(request, item_id):
    if request.method == 'POST':
        try:
            item = get_object_or_404(InventoryItem, id=item_id, hospital__user=request.user)
            quantity = int(request.POST.get('quantity', 0))
            transaction_type = request.POST.get('transaction_type')
            notes = request.POST.get('notes', '')
            
            if transaction_type == 'OUT' and quantity > item.quantity:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Cannot remove more items than available in stock'
                }, status=400)
            
            # Update item quantity
            if transaction_type == 'IN':
                item.quantity += quantity
            elif transaction_type == 'OUT':
                item.quantity -= quantity
            item.save()
            
            # Create transaction record
            InventoryTransaction.objects.create(
                item=item,
                transaction_type=transaction_type,
                quantity=quantity,
                performed_by=request.user,
                notes=notes
            )
            
            messages.success(request, 'Stock updated successfully')
            return JsonResponse({'status': 'success', 'message': 'Stock updated successfully'})
            
        except Exception as e:
            messages.error(request, f'Error updating stock: {str(e)}')
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@login_required
@user_passes_test(is_hospital_staff)
def staff_management(request):
    print("DEBUG: Staff management view accessed")
    try:
        hospital = get_object_or_404(Hospital, user=request.user)
        staff_members = Staff.objects.filter(hospital=hospital)
        
        # Add these debug prints
        print(f"DEBUG: Found {staff_members.count()} staff members")
        print(f"DEBUG: Using template path: {request.resolver_match.view_name}")
        
        # Handle filters
        role = request.GET.get('role')
        department = request.GET.get('department')
        status = request.GET.get('status')
        search = request.GET.get('search')
        
        if role:
            staff_members = staff_members.filter(role=role)
        if department:
            staff_members = staff_members.filter(department=department)
        if status:
            staff_members = staff_members.filter(status=status)
        if search:
            staff_members = staff_members.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(employee_id__icontains=search)
            )
        
        # Pagination
        paginator = Paginator(staff_members, 9)
        page = request.GET.get('page')
        staff_members = paginator.get_page(page)
        
        context = {
            'staff_members': staff_members,
            'roles': dict(Staff.ROLE_CHOICES),
            'departments': dict(Staff.DEPARTMENT_CHOICES),
            'statuses': dict(Staff.STATUS_CHOICES),
            'selected_role': role,
            'selected_department': department,
            'selected_status': status,
            'search_query': search,
            'page': 'staff'
        }
        return render(request, 'authentication/staff_management.html', context)
    except Exception as e:
        messages.error(request, f'Error loading staff management: {str(e)}')
        return redirect('authentication:hospital_dashboard')
@login_required
@user_passes_test(is_hospital_staff)
def add_staff_member(request):
    if request.method == 'POST':
        try:
            print("Received POST request for adding staff member")  # Debug print
            
            # Get the hospital
            hospital = request.user.hospital
            
            # Create user account
            user_data = {
                'username': request.POST.get('username'),
                'email': request.POST.get('email'),
                'password': request.POST.get('password'),
                'first_name': request.POST.get('first_name'),
                'last_name': request.POST.get('last_name'),
            }
            print(f"Creating user with data: {user_data}")  # Debug print
            
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password']
            )
            user.first_name = user_data['first_name']
            user.last_name = user_data['last_name']
            user.save()

            # Generate employee ID
            employee_id = f"EMP{str(uuid.uuid4())[:8].upper()}"
            while Staff.objects.filter(employee_id=employee_id).exists():
                employee_id = f"EMP{str(uuid.uuid4())[:8].upper()}"

            # Create staff member
            staff_data = {
                'user': user,
                'hospital': hospital,
                'employee_id': employee_id,
                'role': request.POST.get('role'),
                'department': request.POST.get('department'),
                'qualification': request.POST.get('qualification', ''),
                'specialization': request.POST.get('specialization', ''),
                'status': 'ACTIVE',
                'joining_date': timezone.now().date(),
            }
            print(f"Creating staff with data: {staff_data}")  # Debug print

            staff = Staff.objects.create(**staff_data)

            response_data = {
                'status': 'success',
                'message': 'Staff member added successfully',
                'staff': {
                    'id': staff.id,
                    'full_name': f"{user.first_name} {user.last_name}",
                    'employee_id': staff.employee_id,
                    'role': staff.role,
                    'role_display': staff.get_role_display(),
                    'department': staff.department,
                    'department_display': staff.get_department_display(),
                    'status': staff.status,
                    'status_display': staff.get_status_display(),
                    'joining_date': staff.joining_date.strftime('%b %d, %Y')
                }
            }
            print(f"Sending response: {response_data}")  # Debug print
            return JsonResponse(response_data)

        except Exception as e:
            print(f"Error adding staff: {str(e)}")  # Debug print
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=400)

@login_required
@user_passes_test(is_hospital_staff)
def edit_staff_member(request, staff_id):
    try:
        hospital = get_object_or_404(Hospital, user=request.user)
        staff = get_object_or_404(Staff, id=staff_id, hospital=hospital)
        
        if request.method == 'POST':
            staff.role = request.POST.get('role')
            staff.department = request.POST.get('department')
            staff.status = request.POST.get('status')
            staff.save()
            
            messages.success(request, 'Staff member updated successfully')
            return redirect('authentication:staff_management')
            
        context = {
            'staff': staff,
            'roles': dict(Staff.ROLE_CHOICES),
            'departments': dict(Staff.DEPARTMENT_CHOICES),
            'statuses': dict(Staff.STATUS_CHOICES)
        }
        return render(request, 'authentication/edit_staff.html', context)
        
    except Exception as e:
        messages.error(request, f'Error updating staff member: {str(e)}')
        return redirect('authentication:staff_management')

@login_required
@user_passes_test(is_hospital_staff)
def delete_staff_member(request, staff_id):
    if request.method == 'POST':
        try:
            hospital = get_object_or_404(Hospital, user=request.user)
            staff = get_object_or_404(Staff, id=staff_id, hospital=hospital)
            
            user = staff.user
            staff.delete()
            user.delete()
            
            messages.success(request, 'Staff member deleted successfully')
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            messages.error(request, f'Error deleting staff member: {str(e)}')
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@login_required
@user_passes_test(is_hospital_staff)
def update_bed_availability(request):
    if request.method == 'POST':
        try:
            hospital = get_object_or_404(Hospital, user=request.user)
            total_beds = int(request.POST.get('total_beds', 0))
            available_beds = int(request.POST.get('available_beds', 0))
            
            if available_beds > total_beds:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Available beds cannot exceed total beds'
                })
            
            hospital.total_beds = total_beds
            hospital.available_beds = available_beds
            hospital.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Bed availability updated successfully'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error updating bed availability: {str(e)}'
            })
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_hospital_staff)
def toggle_emergency_status(request):
    if request.method == 'POST':
        try:
            hospital = get_object_or_404(Hospital, user=request.user)
            hospital.emergency_status = 'CLOSED' if hospital.emergency_status == 'OPEN' else 'OPEN'
            hospital.save()
            
            return JsonResponse({
                'status': 'success',
                'message': f'Emergency status updated to {hospital.emergency_status}',
                'new_status': hospital.emergency_status
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error updating emergency status: {str(e)}'
            })
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def patient_signup_view(request):
    if request.method == 'POST':
        form = PatientSignUpForm(request.POST)
        if form.is_valid():
            # Create user but don't save yet
            user = form.save(commit=False)
            
            # Generate a unique username from email
            email = form.cleaned_data.get('email')
            base_username = email.split('@')[0]
            username = base_username
            counter = 1
            
            # Keep trying until we find a unique username
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
                
            user.username = username
            user.user_type = 'patient'
            user.is_active = False
            user.save()

            # Generate activation token
            current_site = get_current_site(request)
            activation_token = default_token_generator.make_token(user)
            activation_link = f"http://{current_site.domain}/authentication/activate/{urlsafe_base64_encode(force_bytes(user.pk))}/{activation_token}/"

            # Store registration data in session
            request.session['pending_registration'] = {
                'user_id': user.pk,
                'email': user.email,
                'activation_link': activation_link
            }

            # Redirect to Gmail OAuth
            return redirect('authentication:gmail_auth_init')
            
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PatientSignUpForm()
    
    return render(request, 'authentication/patient_signup.html', {'form': form})

@login_required
@user_passes_test(is_hospital_staff)
def get_inventory_stats(request):
    try:
        hospital = get_object_or_404(Hospital, user=request.user)
        items = InventoryItem.objects.filter(hospital=hospital)
        
        stats = {
            'total_items': items.count(),
            'low_stock': items.filter(quantity__lte=F('minimum_stock')).count(),
            'expired': items.filter(expiry_date__lte=timezone.now().date()).count(),
            'total_value': items.aggregate(
                total=Sum(F('quantity') * F('unit_price'))
            )['total'] or 0
        }
        
        return JsonResponse({'status': 'success', 'data': stats})
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error fetching inventory stats: {str(e)}'
        })

@login_required
def hospital_appointments(request):
    appointments = Appointment.objects.filter(
        hospital=request.user.hospital
    ).order_by('appointment_date')  # Changed from appointment_datetime to appointment_date
    
    context = {
        'appointments': appointments,
        'page': 'appointments'
    }
    return render(request, 'authentication/hospital_appointments.html', context)

@login_required
def update_appointment_status(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, hospital=request.user.hospital)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['CONFIRMED', 'CANCELLED', 'COMPLETED']:
            appointment.status = new_status
            appointment.save()
            messages.success(request, f'Appointment status updated to {new_status}')
        
    return redirect('authentication:hospital_appointments')

@login_required
def appointment_calendar(request):
    context = {
        'page': 'appointments'
    }
    return render(request, 'authentication/appointment_calendar.html', context)
def gmail_auth_init(request):
    flow = Flow.from_client_secrets_file(
        settings.GOOGLE_OAUTH2_CLIENT_SECRETS_JSON,
        scopes=[
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/gmail.send'
        ],
        redirect_uri=settings.GOOGLE_OAUTH2_REDIRECT_URI
    )
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    request.session['state'] = state
    return redirect(authorization_url)

import logging
logger = logging.getLogger(__name__)

def oauth2callback(request):
    try:
        flow = Flow.from_client_secrets_file(
            settings.GOOGLE_OAUTH2_CLIENT_SECRETS_JSON,
            scopes=[
                'openid',
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile',
                'https://www.googleapis.com/auth/gmail.send'
            ],
            redirect_uri=settings.GOOGLE_OAUTH2_REDIRECT_URI,
            state=request.session['state']
        )
        
        # Disable scope verification
        flow.oauth2session._client.scope_checker = lambda x: True
        
        try:
            flow.fetch_token(authorization_response=request.build_absolute_uri())
        except Exception as e:
            logger.error(f"Token fetch error: {str(e)}")
            messages.error(request, f"OAuth token error: {str(e)}")
            return redirect('authentication:login')
        
        # Get credentials and store them
        credentials = flow.credentials
        
        # Store credentials in session
        request.session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        # Get the pending registration data
        pending_registration = request.session.get('pending_registration')
        if pending_registration:
            try:
                user_id = pending_registration.get('user_id')
                email = pending_registration.get('email')
                
                # Log the registration data
                logger.info(f"Processing registration for user_id: {user_id}, email: {email}")
                
                # Generate new activation link with correct domain
                user = User.objects.get(pk=user_id)
                activation_token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                activation_link = f"http://{request.get_host()}/authentication/activate/{uid}/{activation_token}/"
                
                # Log the activation link
                logger.info(f"Generated activation link: {activation_link}")
                
                # Send verification email
                subject = "Verify your email address"
                body = f"""
                Hello!
                
                Thank you for registering. Please click on the link below to verify your email address:
                
                {activation_link}
                
                If you did not register for this account, please ignore this email.
                
                Best regards,
                Your Healthcare Team
                """
                
                # Try to send email and log the result
                try:
                    email_sent = send_email(request, email, subject, body)
                    logger.info(f"Email sending attempt result: {email_sent}")
                    
                    if email_sent:
                        messages.success(request, 'Please check your email to verify your account.')
                    else:
                        messages.error(request, 'Failed to send verification email. Please try again.')
                except Exception as e:
                    logger.error(f"Email sending error: {str(e)}")
                    messages.error(request, f"Failed to send email: {str(e)}")
                
                # Clear the pending registration data
                del request.session['pending_registration']
                
            except Exception as e:
                logger.error(f"Registration processing error: {str(e)}")
                messages.error(request, f"Registration error: {str(e)}")
        else:
            logger.warning("No pending registration found in session")
            messages.warning(request, "No registration data found")
            
        return redirect('authentication:login')
        
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        messages.error(request, f'OAuth error: {str(e)}')
        return redirect('authentication:login')

def send_email(request, to_email, subject, body):
    """Send email using Gmail API"""
    creds_dict = request.session.get('credentials')
    if not creds_dict:
        logger.error("No credentials found in session")
        return False
    
    try:
        credentials = Credentials(
            token=creds_dict['token'],
            refresh_token=creds_dict['refresh_token'],
            token_uri=creds_dict['token_uri'],
            client_id=creds_dict['client_id'],
            client_secret=creds_dict['client_secret'],
            scopes=creds_dict['scopes']
        )

        service = build('gmail', 'v1', credentials=credentials)
        
        message = MIMEText(body)
        message['to'] = to_email
        message['subject'] = subject
        message['from'] = "noreply@healthypals.org"
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Email sending error: {str(e)}")
        return False