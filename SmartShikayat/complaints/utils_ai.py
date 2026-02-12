
import requests
import base64
from django.conf import settings

def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

def check_image_ai(image_file):
    """
    Checks if the image is AI-generated using Groq API.
    Returns: (is_ai, confidence_or_message)
    """
    if not settings.GROQ_API_KEY:
        print("Groq API Key missing")
        return False, "API Key missing"

    # Reset file pointer
    image_file.seek(0)
    base64_image = encode_image(image_file)
    image_file.seek(0) # Reset again for subsequent use

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Using Llama 4 Scout vision model (replacement for decommissioned llama-3.2-11b-vision-preview)
    # Model was updated on July 7, 2025 to meta-llama/llama-4-scout-17b-16e-instruct
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Is this image AI-generated? Reply with strictly 'YES' or 'NO'."
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
        "max_tokens": 10
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()['choices'][0]['message']['content'].strip().upper()
        return "YES" in result, result
    except Exception as e:
        print(f"Groq AI Check Error: {e}")
        return False, str(e)

def extract_license_plate(image_file):
    """
    Extracts license plate number from image using Groq API.
    """
    if not settings.GROQ_API_KEY:
        return None

    image_file.seek(0)
    base64_image = encode_image(image_file)
    image_file.seek(0)

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    url = "https://api.groq.com/openai/v1/chat/completions"
    
    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract the vehicle license plate number from this image. Return ONLY the alphanumeric text of the plate with no spaces or special characters. If none found, return 'NONE'."
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
        "max_tokens": 20
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()['choices'][0]['message']['content'].strip().replace(" ", "")
        if "NONE" in result.upper():
            return None
        return result
    except Exception as e:
        print(f"Groq OCR Error: {e}")
        return None

def check_illegal_parking_ai(image_file):
    """
    Checks if the vehicle in the image is parked illegally.
    Returns: (is_illegal, reason)
    """
    if not settings.GROQ_API_KEY:
        return False, "API Key missing"

    image_file.seek(0)
    base64_image = encode_image(image_file)
    image_file.seek(0)

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    url = "https://api.groq.com/openai/v1/chat/completions"
    
    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyze this image for illegal parking. Is the car parked illegally (e.g., no parking zone, blocking driveway, double parked)? Reply with 'YES' or 'NO' followed by a very brief reason."
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
        "max_tokens": 50
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content'].strip()
        is_illegal = "YES" in content.upper()
        return is_illegal, content
    except Exception as e:
        print(f"Groq Parking Check Error: {e}")
        return False, str(e)

def check_garbage_issue_ai(image_file):
    """
    Checks if the image shows garbage-related issues like trash overflow, dirty bins, etc.
    Returns: (is_valid_garbage, reason)
    """
    if not settings.GROQ_API_KEY:
        return False, "API Key missing"

    image_file.seek(0)
    base64_image = encode_image(image_file)
    image_file.seek(0)

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    url = "https://api.groq.com/openai/v1/chat/completions"
    
    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyze this image for garbage-related issues. Does it show trash overflow, overflowing bins, dirty bins, garbage on streets, or waste management problems? Reply with 'YES' if it shows clear garbage issues, or 'NO' if it doesn't show garbage problems. Include a brief reason."
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
        "max_tokens": 50
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content'].strip()
        is_valid = "YES" in content.upper()
        return is_valid, content
    except Exception as e:
        print(f"Groq Garbage Check Error: {e}")
        return False, str(e)


def check_road_damage_ai(image_file):
    """
    Checks if the image shows road damage like potholes, cracks, or bad road conditions.
    Returns: (is_valid_damage, reason)
    """
    if not settings.GROQ_API_KEY:
        return False, "API Key missing"

    image_file.seek(0)
    base64_image = encode_image(image_file)
    image_file.seek(0)

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    url = "https://api.groq.com/openai/v1/chat/completions"
    
    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyze this image for road damage. Does it show potholes, deep cracks, broken pavement, or bad road conditions? Reply with 'YES' if it shows clear road damage, or 'NO' if it doesn't. Include a brief reason."
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
        "max_tokens": 50
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content'].strip()
        is_valid = "YES" in content.upper()
        return is_valid, content
    except Exception as e:
        print(f"Groq Road Damage Check Error: {e}")
        return False, str(e)

