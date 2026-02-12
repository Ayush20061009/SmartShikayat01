from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json

@login_required
def extract_plate_ajax(request):
    """
    AJAX endpoint to extract license plate from uploaded image
    """
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            from .utils_ai import extract_license_plate
            
            image_file = request.FILES['image']
            user_lang = getattr(request.user, 'preferred_language', 'en') or 'en'
            
            # Extract license plate
            plate_number, confidence, processing_time = extract_license_plate(image_file, language=user_lang)
            
            if plate_number:
                return JsonResponse({
                    'success': True,
                    'plate_number': plate_number,
                    'confidence': confidence,
                    'processing_time': processing_time
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'No license plate detected in the image'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request'
    })
