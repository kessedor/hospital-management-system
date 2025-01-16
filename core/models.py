from django.db import models
from authentication.models import User, Hospital

class Appointment(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateTimeField()
    reason = models.TextField()
    status = models.CharField(max_length=20, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient.username} - {self.hospital.name} - {self.appointment_date}"

class Schedule(models.Model):
    SHIFT_CHOICES = [
        ('MORNING', 'Morning (6AM-2PM)'),
        ('AFTERNOON', 'Afternoon (2PM-10PM)'),
        ('NIGHT', 'Night (10PM-6AM)'),
    ]

    staff = models.ForeignKey('authentication.Staff', on_delete=models.CASCADE, related_name='schedules')
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    date = models.DateField()
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['staff', 'date', 'shift']
        ordering = ['date', 'shift']

    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.date} - {self.shift}"

class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    staff = models.ForeignKey('authentication.Staff', on_delete=models.CASCADE, related_name='leave_requests')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.start_date} to {self.end_date}"