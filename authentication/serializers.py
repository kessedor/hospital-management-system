from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Hospital, Doctor, Patient, EmergencyAlert

User = get_user_model()

class HospitalRegistrationSerializer(serializers.ModelSerializer):
    # Admin user details
    admin_email = serializers.EmailField(write_only=True)
    admin_password = serializers.CharField(write_only=True)
    admin_phone = serializers.CharField(write_only=True)
    admin_first_name = serializers.CharField(write_only=True)
    admin_last_name = serializers.CharField(write_only=True)
    
    class Meta:
        model = Hospital
        fields = [
            'name', 'registration_number', 'address',
            'primary_phone', 'secondary_phone', 'emergency_phone',
            'email', 'total_beds', 'admin_email', 'admin_password',
            'admin_phone', 'admin_first_name', 'admin_last_name'
        ]
        extra_kwargs = {
            'available_beds': {'read_only': True},
            'emergency_status': {'read_only': True},
        }

    def validate(self, data):
        # Add any custom validation here
        return data

    def create(self, validated_data):
        # Extract admin data
        admin_data = {
            'email': validated_data.pop('admin_email', ''),
            'password': validated_data.pop('admin_password', ''),
            'phone_number': validated_data.pop('admin_phone', ''),
            'first_name': validated_data.pop('admin_first_name', ''),
            'last_name': validated_data.pop('admin_last_name', ''),
        }
        admin_data['username'] = admin_data['email']  # Use email as username

        # Create hospital
        hospital = Hospital.objects.create(**validated_data)

        # Create admin user
        User.objects.create_user(
            **admin_data,
            user_type='HOSPITAL_ADMIN',
            hospital=hospital,
            is_staff=True
        )

        return hospital

class StaffMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 
                 'phone_number', 'user_type', 'is_active']

class DoctorScheduleSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Doctor
        fields = ['id', 'doctor_name', 'specialization', 'is_available',
                 'working_hours', 'next_available_slot', 'consultation_fee']

class EmergencyAlertSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    
    class Meta:
        model = EmergencyAlert
        fields = ['id', 'alert_type', 'description', 'location',
                 'patient_name', 'created_at', 'status']

class HospitalDashboardSerializer(serializers.ModelSerializer):
    staff_count = serializers.SerializerMethodField()
    available_beds = serializers.IntegerField()
    active_emergencies = serializers.SerializerMethodField()
    today_appointments = serializers.SerializerMethodField()
    bed_occupancy_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = Hospital
        fields = [
            'id', 'name', 'total_beds', 'available_beds',
            'staff_count', 'active_emergencies', 'today_appointments',
            'bed_occupancy_rate', 'emergency_status'
        ]
    
    def get_staff_count(self, obj):
        return obj.user_set.count()
    
    def get_active_emergencies(self, obj):
        return obj.emergencyalert_set.filter(status='NEW').count()
    
    def get_today_appointments(self, obj):
        from django.utils import timezone
        today = timezone.now().date()
        # Implement appointment counting logic here
        return 0
    
    def get_bed_occupancy_rate(self, obj):
        if obj.total_beds == 0:
            return 0
        return ((obj.total_beds - obj.available_beds) / obj.total_beds) * 100

class BedAvailabilityUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ['available_beds', 'emergency_status']