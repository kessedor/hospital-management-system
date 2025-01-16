from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from authentication.models import Hospital, Staff, User
from .forms import (
    HospitalRegistrationForm, 
    StaffCreationForm, 
    StaffUpdateForm,
    ScheduleForm,
    LeaveRequestForm
)
from .models import Schedule, LeaveRequest
from datetime import datetime, timedelta
import calendar
import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from authentication.models import Hospital, Staff, User
from .forms import HospitalRegistrationForm, StaffCreationForm, StaffUpdateForm

def public_homepage(request):
    hospitals = Hospital.objects.all()
    context = {
        'hospitals': hospitals,
    }
    return render(request, 'core/public_homepage.html', context)

def register_hospital(request):
    if request.method == 'POST':
        form = HospitalRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('public_homepage')
    else:
        form = HospitalRegistrationForm()
    return render(request, 'core/register_hospital.html', {'form': form})

@login_required
def hospital_dashboard(request):
    try:
        if not hasattr(request.user, 'hospital'):
            return render(request, 'core/error.html', {
                'error_message': 'You do not have access to the hospital dashboard. Please contact an administrator.'
            })
        
        hospital = request.user.hospital
        total_staff = Staff.objects.filter(hospital=hospital).count()
        total_patients = hospital.patients.count()
        occupancy_rate = (
            ((hospital.total_beds - hospital.available_beds) / hospital.total_beds * 100)
            if hospital.total_beds > 0 else 0
        )
        
        context = {
            'hospital': hospital,
            'total_staff': total_staff,
            'total_patients': total_patients,
            'available_beds': hospital.available_beds,
            'total_beds': hospital.total_beds,
            'occupancy_rate': round(occupancy_rate, 1),
            'emergency_status': hospital.emergency_status,
        }
        return render(request, 'core/hospital_dashboard.html', context)
    except Exception as e:
        return render(request, 'core/error.html', {
            'error_message': f'An error occurred: {str(e)}'
        })

# Staff Management Views
@login_required
def staff_list(request):
    try:
        if not hasattr(request.user, 'hospital'):
            return render(request, 'core/error.html', {
                'error_message': 'Access denied. Hospital access required.'
            })
        
        hospital = request.user.hospital
        staff_members = Staff.objects.filter(hospital=hospital).select_related('user')

        # Search functionality
        search_query = request.GET.get('search', '')
        if search_query:
            staff_members = staff_members.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(employee_id__icontains=search_query) |
                Q(user__email__icontains=search_query)
            )

        # Filter by department
        department = request.GET.get('department', '')
        if department:
            staff_members = staff_members.filter(department=department)

        # Filter by role
        role = request.GET.get('role', '')
        if role:
            staff_members = staff_members.filter(role=role)

        # Filter by status
        status = request.GET.get('status', '')
        if status:
            staff_members = staff_members.filter(status=status)

        # Sorting
        sort_by = request.GET.get('sort', 'user__first_name')
        staff_members = staff_members.order_by(sort_by)

        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(staff_members, 9)  # Show 9 staff members per page
        
        try:
            staff_members = paginator.page(page)
        except PageNotAnInteger:
            staff_members = paginator.page(1)
        except EmptyPage:
            staff_members = paginator.page(paginator.num_pages)

        # Statistics
        total_staff = Staff.objects.filter(hospital=hospital).count()
        active_staff = Staff.objects.filter(hospital=hospital, status='ACTIVE').count()
        
        context = {
            'staff_members': staff_members,
            'total_staff': total_staff,
            'active_staff': active_staff,
            'departments': Staff.DEPARTMENT_CHOICES,
            'roles': Staff.ROLE_CHOICES,
            'current_filters': {
                'search': search_query,
                'department': department,
                'role': role,
                'status': status,
                'sort': sort_by,
            },
        }
        return render(request, 'core/staff/list.html', context)
    except Exception as e:
        return render(request, 'core/error.html', {
            'error_message': f'An error occurred: {str(e)}'
        })

@login_required
def staff_create(request):
    try:
        if not hasattr(request.user, 'hospital'):
            return render(request, 'core/error.html', {
                'error_message': 'Access denied. Hospital access required.'
            })
        
        if request.method == 'POST':
            form = StaffCreationForm(request.POST)
            if form.is_valid():
                staff = form.save(commit=False)
                staff.hospital = request.user.hospital
                staff.save()
                messages.success(request, 'Staff member created successfully.')
                return redirect('staff_detail', employee_id=staff.employee_id)
        else:
            form = StaffCreationForm()
        
        context = {
            'form': form,
            'departments': Staff.DEPARTMENT_CHOICES,
            'roles': Staff.ROLE_CHOICES,
        }
        return render(request, 'core/staff/create.html', context)
    except Exception as e:
        return render(request, 'core/error.html', {
            'error_message': f'An error occurred: {str(e)}'
        })

@login_required
def staff_detail(request, employee_id):
    try:
        if not hasattr(request.user, 'hospital'):
            return render(request, 'core/error.html', {
                'error_message': 'Access denied. Hospital access required.'
            })
        
        staff = get_object_or_404(
            Staff.objects.select_related('user'),
            hospital=request.user.hospital,
            employee_id=employee_id
        )
        
        context = {
            'staff': staff,
            'assigned_patients': staff.patients.all() if staff.role == 'DOCTOR' else None,
        }
        return render(request, 'core/staff/detail.html', context)
    except Exception as e:
        return render(request, 'core/error.html', {
            'error_message': f'An error occurred: {str(e)}'
        })

@login_required
def staff_update(request, employee_id):
    try:
        if not hasattr(request.user, 'hospital'):
            return render(request, 'core/error.html', {
                'error_message': 'Access denied. Hospital access required.'
            })
        
        staff = get_object_or_404(Staff, hospital=request.user.hospital, employee_id=employee_id)
        
        if request.method == 'POST':
            form = StaffUpdateForm(request.POST, instance=staff)
            if form.is_valid():
                form.save()
                messages.success(request, 'Staff information updated successfully.')
                return redirect('staff_detail', employee_id=staff.employee_id)
        else:
            form = StaffUpdateForm(instance=staff)
        
        context = {
            'form': form,
            'staff': staff,
            'departments': Staff.DEPARTMENT_CHOICES,
            'roles': Staff.ROLE_CHOICES,
        }
        return render(request, 'core/staff/update.html', context)
    except Exception as e:
        return render(request, 'core/error.html', {
            'error_message': f'An error occurred: {str(e)}'
        })

@login_required
def staff_delete(request, employee_id):
    try:
        if not hasattr(request.user, 'hospital'):
            return render(request, 'core/error.html', {
                'error_message': 'Access denied. Hospital access required.'
            })
        
        staff = get_object_or_404(Staff, hospital=request.user.hospital, employee_id=employee_id)
        
        if request.method == 'POST':
            staff.status = 'INACTIVE'
            staff.save()
            messages.success(request, 'Staff member deactivated successfully.')
            return redirect('staff_list')
        
        return render(request, 'core/staff/delete.html', {'staff': staff})
    except Exception as e:
        return render(request, 'core/error.html', {
            'error_message': f'An error occurred: {str(e)}'
        })
# Schedule Management Views
@login_required
def schedule_list(request):
    try:
        if not hasattr(request.user, 'hospital'):
            return render(request, 'core/error.html', {
                'error_message': 'Access denied. Hospital access required.'
            })
        
        hospital = request.user.hospital
        schedules = Schedule.objects.filter(hospital=hospital).select_related('staff__user')
        
        # Filter by staff member
        staff_id = request.GET.get('staff', '')
        if staff_id:
            schedules = schedules.filter(staff__employee_id=staff_id)
        
        # Filter by date range
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        if start_date and end_date:
            schedules = schedules.filter(date__range=[start_date, end_date])
        
        # Filter by shift
        shift = request.GET.get('shift', '')
        if shift:
            schedules = schedules.filter(shift=shift)
        
        context = {
            'schedules': schedules,
            'staff_members': Staff.objects.filter(hospital=hospital, status='ACTIVE'),
            'shifts': Schedule.SHIFT_CHOICES,
        }
        return render(request, 'core/schedule/list.html', context)
    except Exception as e:
        return render(request, 'core/error.html', {
            'error_message': f'An error occurred: {str(e)}'
        })

@login_required
def schedule_create(request):
    try:
        if not hasattr(request.user, 'hospital'):
            return render(request, 'core/error.html', {
                'error_message': 'Access denied. Hospital access required.'
            })
        
        if request.method == 'POST':
            form = ScheduleForm(request.POST)
            if form.is_valid():
                schedule = form.save(commit=False)
                schedule.hospital = request.user.hospital
                schedule.save()
                messages.success(request, 'Schedule created successfully.')
                return redirect('schedule_list')
        else:
            form = ScheduleForm()
            form.fields['staff'].queryset = Staff.objects.filter(
                hospital=request.user.hospital,
                status='ACTIVE'
            )
        
        context = {
            'form': form,
            'shifts': Schedule.SHIFT_CHOICES,
        }
        return render(request, 'core/schedule/create.html', context)
    except Exception as e:
        return render(request, 'core/error.html', {
            'error_message': f'An error occurred: {str(e)}'
        })

@login_required
def schedule_weekly(request):
    try:
        if not hasattr(request.user, 'hospital'):
            return render(request, 'core/error.html', {
                'error_message': 'Access denied. Hospital access required.'
            })
        
        hospital = request.user.hospital
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        schedules = Schedule.objects.filter(
            hospital=hospital,
            date__range=[week_start, week_end]
        ).select_related('staff__user')
        
        # Organize schedules by day and shift
        weekly_schedule = {}
        for i in range(7):
            day = week_start + timedelta(days=i)
            weekly_schedule[day] = {
                'MORNING': schedules.filter(date=day, shift='MORNING'),
                'AFTERNOON': schedules.filter(date=day, shift='AFTERNOON'),
                'NIGHT': schedules.filter(date=day, shift='NIGHT'),
            }
        
        context = {
            'weekly_schedule': weekly_schedule,
            'week_start': week_start,
            'week_end': week_end,
        }
        return render(request, 'core/schedule/weekly.html', context)
    except Exception as e:
        return render(request, 'core/error.html', {
            'error_message': f'An error occurred: {str(e)}'
        })

@login_required
def schedule_export(request):
    try:
        if not hasattr(request.user, 'hospital'):
            return HttpResponse('Access denied', status=403)
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="schedule.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Date', 'Staff', 'Shift', 'Status'])
        
        schedules = Schedule.objects.filter(hospital=request.user.hospital).select_related('staff__user')
        for schedule in schedules:
            writer.writerow([
                schedule.date,
                schedule.staff.user.get_full_name(),
                schedule.shift,
                'Approved' if schedule.is_approved else 'Pending'
            ])
        
        return response
    except Exception as e:
        return HttpResponse(f'Error: {str(e)}', status=500)

# Leave Management Views
@login_required
def leave_list(request):
    try:
        if not hasattr(request.user, 'hospital'):
            return render(request, 'core/error.html', {
                'error_message': 'Access denied. Hospital access required.'
            })
        
        hospital = request.user.hospital
        leave_requests = LeaveRequest.objects.filter(
            staff__hospital=hospital
        ).select_related('staff__user')
        
        context = {
            'leave_requests': leave_requests,
        }
        return render(request, 'core/leave/list.html', context)
    except Exception as e:
        return render(request, 'core/error.html', {
            'error_message': f'An error occurred: {str(e)}'
        })

@login_required
def leave_request(request):
    try:
        if not hasattr(request.user, 'staff'):
            return render(request, 'core/error.html', {
                'error_message': 'Access denied. Staff access required.'
            })
        
        if request.method == 'POST':
            form = LeaveRequestForm(request.POST)
            if form.is_valid():
                leave_request = form.save(commit=False)
                leave_request.staff = request.user.staff
                leave_request.save()
                messages.success(request, 'Leave request submitted successfully.')
                return redirect('leave_list')
        else:
            form = LeaveRequestForm()
        
        context = {
            'form': form,
        }
        return render(request, 'core/leave/request.html', context)
    except Exception as e:
        return render(request, 'core/error.html', {
            'error_message': f'An error occurred: {str(e)}'
        })
@login_required
def leave_approve(request, pk):
    try:
        if not hasattr(request.user, 'hospital'):
            return render(request, 'core/error.html', {
                'error_message': 'Access denied. Hospital access required.'
            })
        
        leave_request = get_object_or_404(
            LeaveRequest, 
            pk=pk, 
            staff__hospital=request.user.hospital
        )
        
        if request.method == 'POST':
            leave_request.status = 'APPROVED'
            leave_request.approved_by = request.user
            leave_request.approved_at = timezone.now()
            leave_request.save()
            
            # Update staff status if needed
            if leave_request.start_date <= timezone.now().date():
                leave_request.staff.status = 'ON_LEAVE'
                leave_request.staff.save()
            
            messages.success(request, 'Leave request approved successfully.')
        
        return redirect('leave_list')
    except Exception as e:
        return render(request, 'core/error.html', {
            'error_message': f'An error occurred: {str(e)}'
        })
@login_required
def leave_approve(request, pk):
    try:
        if not hasattr(request.user, 'hospital'):
            return render(request, 'core/error.html', {
                'error_message': 'Access denied. Hospital access required.'
            })
        
        leave_request = get_object_or_404(
            LeaveRequest, 
            pk=pk, 
            staff__hospital=request.user.hospital
        )
        
        if request.method == 'POST':
            leave_request.status = 'APPROVED'
            leave_request.approved_by = request.user
            leave_request.approved_at = timezone.now()
            leave_request.save()
            
            # Update staff status if needed
            if leave_request.start_date <= timezone.now().date():
                leave_request.staff.status = 'ON_LEAVE'
                leave_request.staff.save()
            
            messages.success(request, 'Leave request approved successfully.')
        
        return redirect('leave_list')
    except Exception as e:
        return render(request, 'core/error.html', {
            'error_message': f'An error occurred: {str(e)}'
        })

@login_required
def leave_reject(request, pk):
    try:
        if not hasattr(request.user, 'hospital'):
            return render(request, 'core/error.html', {
                'error_message': 'Access denied. Hospital access required.'
            })
        
        leave_request = get_object_or_404(
            LeaveRequest, 
            pk=pk, 
            staff__hospital=request.user.hospital
        )
        
        if request.method == 'POST':
            leave_request.status = 'REJECTED'
            leave_request.approved_by = request.user
            leave_request.approved_at = timezone.now()
            leave_request.save()
            
            messages.success(request, 'Leave request rejected successfully.')
        
        return redirect('leave_list')
    except Exception as e:
        return render(request, 'core/error.html', {
            'error_message': f'An error occurred: {str(e)}'
        })
@login_required
def update_bed_availability(request):
    try:
        if not hasattr(request.user, 'hospital'):
            return render(request, 'core/error.html', {
                'error_message': 'Access denied. Hospital access required.'
            })
        
        if request.method == 'POST':
            available_beds = request.POST.get('available_beds')
            if available_beds is not None:
                hospital = request.user.hospital
                hospital.available_beds = int(available_beds)
                hospital.save()
                messages.success(request, 'Bed availability updated successfully.')
            else:
                messages.error(request, 'Invalid bed count provided.')
        
        return redirect('hospital_dashboard')
    except Exception as e:
        return render(request, 'core/error.html', {
            'error_message': f'An error occurred: {str(e)}'
        })

@login_required
def toggle_emergency_status(request):
    try:
        if not hasattr(request.user, 'hospital'):
            return render(request, 'core/error.html', {
                'error_message': 'Access denied. Hospital access required.'
            })
        
        if request.method == 'POST':
            hospital = request.user.hospital
            # Toggle between OPEN and CLOSED
            hospital.emergency_status = 'CLOSED' if hospital.emergency_status == 'OPEN' else 'OPEN'
            hospital.save()
            
            status_message = 'opened' if hospital.emergency_status == 'OPEN' else 'closed'
            messages.success(request, f'Emergency department {status_message} successfully.')
        
        return redirect('hospital_dashboard')
    except Exception as e:
        return render(request, 'core/error.html', {
            'error_message': f'An error occurred: {str(e)}'
        })
# Add these at the end of your existing views.py file

def handler403(request, exception=None):
    context = {
        'error_code': 403,
        'error_message': 'Access Forbidden',
        'error_details': 'You do not have permission to access this resource.'
    }
    return render(request, 'core/error.html', context, status=403)

def handler404(request, exception=None):
    context = {
        'error_code': 404,
        'error_message': 'Page Not Found',
        'error_details': 'The requested page could not be found.'
    }
    return render(request, 'core/error.html', context, status=404)

def handler500(request):
    context = {
        'error_code': 500,
        'error_message': 'Server Error',
        'error_details': 'An internal server error occurred.'
    }
    return render(request, 'core/error.html', context, status=500)