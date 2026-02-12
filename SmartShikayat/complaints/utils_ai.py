
import requests
import base64
import time
import re
from django.conf import settings

# Language translations for AI prompts
LANGUAGE_PROMPTS = {
    'en': {
        'ai_check': "Is this image AI-generated? Reply with strictly 'YES' or 'NO'.",
        'parking': "Analyze this image for illegal parking. Is the car parked illegally (e.g., no parking zone, blocking driveway, double parked)? Reply with 'YES' or 'NO' followed by a very brief reason.",
        'road': "Analyze this image for road damage. Is there visible road damage such as potholes, cracks, broken pavement, or deteriorated road surface? Reply with 'YES' or 'NO' followed by a brief description of what you see.",
        'garbage': "Analyze this image for garbage/waste issues. Is there visible garbage accumulation, littering, overflowing bins, or unsanitary waste conditions? Reply with 'YES' or 'NO' followed by a brief description.",
        'plate': "Extract the vehicle license plate number from this image. Return ONLY the alphanumeric text of the plate with no spaces or special characters. If none found, return 'NONE'."
    },
    'hi': {
        'ai_check': "क्या यह छवि AI द्वारा बनाई गई है? केवल 'YES' या 'NO' में उत्तर दें।",
        'parking': "अवैध पार्किंग के लिए इस छवि का विश्लेषण करें। क्या कार अवैध रूप से पार्क की गई है (जैसे, नो पार्किंग ज़ोन, ड्राइववे को ब्लॉक करना)? 'YES' या 'NO' के साथ संक्षिप्त कारण दें।",
        'road': "सड़क क्षति के लिए इस छवि का विश्लेषण करें। क्या गड्ढे, दरारें, टूटी हुई सड़क दिखाई दे रही है? 'YES' या 'NO' के साथ संक्षिप्त विवरण दें।",
        'garbage': "कचरे की समस्या के लिए इस छवि का विश्लेषण करें। क्या कचरा जमा, गंदगी दिखाई दे रही है? 'YES' या 'NO' के साथ संक्षिप्त विवरण दें।",
        'plate': "इस छवि से वाहन नंबर प्लेट निकालें। केवल अल्फान्यूमेरिक टेक्स्ट लौटाएं। यदि नहीं मिला, तो 'NONE' लौटाएं।"
    },
    'es': {
        'ai_check': "¿Esta imagen fue generada por IA? Responde estrictamente con 'YES' o 'NO'.",
        'parking': "Analiza esta imagen para estacionamiento ilegal. ¿El auto está estacionado ilegalmente? Responde con 'YES' o 'NO' seguido de una breve razón.",
        'road': "Analiza esta imagen para daños en la carretera. ¿Hay baches, grietas o pavimento roto visible? Responde con 'YES' o 'NO' seguido de una breve descripción.",
        'garbage': "Analiza esta imagen para problemas de basura. ¿Hay acumulación de basura visible? Responde con 'YES' o 'NO' seguido de una breve descripción.",
        'plate': "Extrae el número de matrícula del vehículo de esta imagen. Devuelve SOLO el texto alfanumérico. Si no se encuentra, devuelve 'NONE'."
    }
}

def extract_confidence_from_response(response_text):
    """
    Attempts to extract confidence score from AI response.
    Returns a score between 0-100.
    """
    # Look for patterns like "confidence: 85%" or "85% confident"
    patterns = [
        r'confidence[:\s]+(\d+)%',
        r'(\d+)%\s+confident',
        r'certainty[:\s]+(\d+)%'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, response_text.lower())
        if match:
            return float(match.group(1))
    
    # If YES is in response, assume high confidence, otherwise medium
    if "YES" in response_text.upper():
        return 85.0
    elif "NO" in response_text.upper():
        return 75.0
    else:
        return 50.0

def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')


def check_image_ai(image_file, language='en'):
    """
    Checks if the image is AI-generated using Groq API.
    Returns: (is_ai, message, confidence, processing_time_ms)
    """
    if not settings.GROQ_API_KEY:
        print("Groq API Key missing")
        return False, "API Key missing", 0.0, 0

    start_time = time.time()
    
    # Reset file pointer
    image_file.seek(0)
    base64_image = encode_image(image_file)
    image_file.seek(0)

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Get prompt in requested language
    prompt_text = LANGUAGE_PROMPTS.get(language, LANGUAGE_PROMPTS['en'])['ai_check']
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt_text
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.1,
        "max_tokens": 300  # Increased from 10 to allow proper responses
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()['choices'][0]['message']['content'].strip().upper()
        
        processing_time = int((time.time() - start_time) * 1000)
        confidence = extract_confidence_from_response(result)
        
        return "YES" in result, result, confidence, processing_time
    except requests.exceptions.HTTPError as e:
        print(f"Groq AI Check HTTP Error: {e}")
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        processing_time = int((time.time() - start_time) * 1000)
        return False, f"API Error: {response.status_code}", 0.0, processing_time
    except Exception as e:
        print(f"Groq AI Check Error: {e}")
        processing_time = int((time.time() - start_time) * 1000)
        return False, str(e), 0.0, processing_time

def extract_license_plate(image_file, language='en'):
    """
    Extracts license plate number from image using Groq API.
    Returns: (plate_number, confidence, processing_time_ms)
    """
    if not settings.GROQ_API_KEY:
        return None, 0.0, 0

    start_time = time.time()
    
    image_file.seek(0)
    base64_image = encode_image(image_file)
    image_file.seek(0)

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt_text = LANGUAGE_PROMPTS.get(language, LANGUAGE_PROMPTS['en'])['plate']
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt_text
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.1,
        "max_tokens": 100  # Increased for better OCR results
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()['choices'][0]['message']['content'].strip().replace(" ", "")
        
        processing_time = int((time.time() - start_time) * 1000)
        
        if "NONE" in result.upper():
            return None, 0.0, processing_time
        
        confidence = 80.0  # OCR typically has good confidence when it detects something
        return result, confidence, processing_time
    except requests.exceptions.HTTPError as e:
        print(f"Groq OCR HTTP Error: {e}")
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        processing_time = int((time.time() - start_time) * 1000)
        return None, 0.0, processing_time
    except Exception as e:
        print(f"Groq OCR Error: {e}")
        processing_time = int((time.time() - start_time) * 1000)
        return None, 0.0, processing_time

def check_illegal_parking_ai(image_file, language='en'):
    """
    Checks if the vehicle in the image is parked illegally.
    Returns: (is_illegal, reason, confidence, processing_time_ms)
    """
    if not settings.GROQ_API_KEY:
        return False, "API Key missing", 0.0, 0

    start_time = time.time()
    
    image_file.seek(0)
    base64_image = encode_image(image_file)
    image_file.seek(0)

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt_text = LANGUAGE_PROMPTS.get(language, LANGUAGE_PROMPTS['en'])['parking']
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt_text
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.1,
        "max_tokens": 300  # Increased for detailed responses
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content'].strip()
        
        processing_time = int((time.time() - start_time) * 1000)
        confidence = extract_confidence_from_response(content)
        is_illegal = "YES" in content.upper()
        
        return is_illegal, content, confidence, processing_time
    except requests.exceptions.HTTPError as e:
        print(f"Groq Parking Check HTTP Error: {e}")
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        processing_time = int((time.time() - start_time) * 1000)
        return False, f"API Error: {response.status_code}", 0.0, processing_time
    except Exception as e:
        print(f"Groq Parking Check Error: {e}")
        processing_time = int((time.time() - start_time) * 1000)
        return False, str(e), 0.0, processing_time

def check_road_damage_ai(image_file, language='en'):
    """
    Checks if the image shows actual road damage (potholes, cracks, etc.).
    Returns: (is_damaged, reason, confidence, processing_time_ms)
    """
    if not settings.GROQ_API_KEY:
        return False, "API Key missing", 0.0, 0

    start_time = time.time()
    
    image_file.seek(0)
    base64_image = encode_image(image_file)
    image_file.seek(0)

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt_text = LANGUAGE_PROMPTS.get(language, LANGUAGE_PROMPTS['en'])['road']
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt_text
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.1,
        "max_tokens": 300  # Increased for detailed responses
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content'].strip()
        
        processing_time = int((time.time() - start_time) * 1000)
        confidence = extract_confidence_from_response(content)
        is_damaged = "YES" in content.upper()
        
        return is_damaged, content, confidence, processing_time
    except requests.exceptions.HTTPError as e:
        print(f"Groq Road Damage Check HTTP Error: {e}")
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        processing_time = int((time.time() - start_time) * 1000)
        return False, f"API Error: {response.status_code}", 0.0, processing_time
    except Exception as e:
        print(f"Groq Road Damage Check Error: {e}")
        processing_time = int((time.time() - start_time) * 1000)
        return False, str(e), 0.0, processing_time

def check_garbage_issue_ai(image_file, language='en'):
    """
    Checks if the image shows a legitimate garbage/waste issue.
    Returns: (is_garbage_issue, reason, confidence, processing_time_ms)
    """
    if not settings.GROQ_API_KEY:
        return False, "API Key missing", 0.0, 0

    start_time = time.time()
    
    image_file.seek(0)
    base64_image = encode_image(image_file)
    image_file.seek(0)

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt_text = LANGUAGE_PROMPTS.get(language, LANGUAGE_PROMPTS['en'])['garbage']
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt_text
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.1,
        "max_tokens": 300  # Increased for detailed responses
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content'].strip()
        
        processing_time = int((time.time() - start_time) * 1000)
        confidence = extract_confidence_from_response(content)
        is_garbage_issue = "YES" in content.upper()
        
        return is_garbage_issue, content, confidence, processing_time
    except requests.exceptions.HTTPError as e:
        print(f"Groq Garbage Check HTTP Error: {e}")
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        processing_time = int((time.time() - start_time) * 1000)
        return False, f"API Error: {response.status_code}", 0.0, processing_time
    except Exception as e:
        print(f"Groq Garbage Check Error: {e}")
        processing_time = int((time.time() - start_time) * 1000)
        return False, str(e), 0.0, processing_time




