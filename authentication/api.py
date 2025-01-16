from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import Hospital
from math import radians, sin, cos, sqrt, atan2
import json
import logging

logger = logging.getLogger(__name__)

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return distance

@csrf_exempt
@require_http_methods(["GET"])
def nearby_hospitals(request):
    try:
        # Log the incoming request parameters
        lat = request.GET.get('lat')
        lng = request.GET.get('lng')
        
        logger.info(f"Received request for nearby hospitals. Lat: {lat}, Lng: {lng}")
        
        if not lat or not lng:
            return JsonResponse({
                'error': 'Missing coordinates',
                'message': 'Latitude and longitude are required'
            }, status=400)

        lat = float(lat)
        lng = float(lng)
        
        # Get all hospitals
        hospitals = Hospital.objects.all()
        logger.info(f"Found {hospitals.count()} hospitals in database")
        
        nearby = []
        for hospital in hospitals:
            try:
                distance = calculate_distance(
                    lat, lng,
                    float(hospital.latitude), float(hospital.longitude)
                )
                
                if distance <= 10:  # Within 10km radius
                    nearby.append({
                        'id': hospital.id,
                        'name': hospital.name,
                        'distance': round(distance, 2),
                        'available_beds': hospital.available_beds,
                        'address': hospital.address,
                        'phone': hospital.primary_phone,
                        'emergency_status': 'OPEN'
                    })
            except Exception as e:
                logger.error(f"Error processing hospital {hospital.id}: {str(e)}")
                continue
        
        logger.info(f"Found {len(nearby)} nearby hospitals")
        
        # Sort by distance
        nearby.sort(key=lambda x: x['distance'])
        
        # Return at least some hospitals even if they're far
        if not nearby and hospitals.exists():
            logger.info("No nearby hospitals found, returning all hospitals")
            nearby = [{
                'id': hospital.id,
                'name': hospital.name,
                'distance': 999,  # placeholder distance
                'available_beds': hospital.available_beds,
                'address': hospital.address,
                'phone': hospital.primary_phone,
                'emergency_status': 'OPEN'
            } for hospital in hospitals[:5]]  # Return top 5 hospitals
        
        return JsonResponse(nearby, safe=False)
    
    except Exception as e:
        logger.error(f"Error in nearby_hospitals: {str(e)}")
        return JsonResponse({
            'error': str(e),
            'message': 'Error finding nearby hospitals'
        }, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def create_emergency_alert(request):
    try:
        data = json.loads(request.body)
        logger.info(f"Received emergency alert: {data}")
        # Here we'll implement alert creation later
        return JsonResponse({'success': True})
    except Exception as e:
        logger.error(f"Error creating emergency alert: {str(e)}")
        return JsonResponse({
            'error': str(e),
            'message': 'Error creating emergency alert'
        }, status=400)