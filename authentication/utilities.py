from .models import Hospital

def is_hospital_staff(user):
    if not user.is_authenticated:
        return False
    try:
        return hasattr(user, 'hospital') and user.hospital is not None
    except:
        return False