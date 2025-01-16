from django.db import models

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    TIME_SLOTS = [
        ('0900', '9:00 AM'),
        ('1000', '10:00 AM'),
        ('1100', '11:00 AM'),
        ('1400', '2:00 PM'),
        ('1500', '3:00 PM'),
        ('1600', '4:00 PM'),
    ]
    
    patient = models.ForeignKey('authentication.Patient', on_delete=models.CASCADE)
    hospital = models.ForeignKey('authentication.Hospital', on_delete=models.CASCADE)
    department = models.ForeignKey('authentication.Department', on_delete=models.CASCADE)
    appointment_date = models.DateField()
    time_slot = models.CharField(max_length=4, choices=TIME_SLOTS)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['department', 'appointment_date', 'time_slot']