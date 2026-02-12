import os
import sys
import django
import base64
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartShikayat.settings')
django.setup()

from django.conf import settings

def test_groq_api():
    """Test the Groq API with a simple text request first"""
    
    print("=" * 60)
    print("GROQ API TEST")
    print("=" * 60)
    
    api_key = settings.GROQ_API_KEY
    print(f"\n✓ API Key loaded: {api_key[:20]}...")
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test 1: Simple text-only request
    print("\n" + "=" * 60)
    print("TEST 1: Simple Text Request")
    print("=" * 60)
    
    payload = {
        "model": "llama-3.2-11b-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": "Say 'Hello, API is working!'"
            }
        ],
        "temperature": 0.1,
        "max_tokens": 50
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ SUCCESS!")
            print(f"Response: {result['choices'][0]['message']['content']}")
        else:
            print(f"✗ FAILED!")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"✗ EXCEPTION: {e}")
    
    # Test 2: Check available models
    print("\n" + "=" * 60)
    print("TEST 2: List Available Models")
    print("=" * 60)
    
    try:
        models_url = "https://api.groq.com/openai/v1/models"
        response = requests.get(models_url, headers=headers)
        
        if response.status_code == 200:
            models = response.json()
            print("✓ Available models:")
            for model in models.get('data', []):
                model_id = model.get('id', 'unknown')
                if 'vision' in model_id.lower() or 'llama' in model_id.lower():
                    print(f"  - {model_id}")
        else:
            print(f"✗ Failed to get models: {response.text}")
            
    except Exception as e:
        print(f"✗ EXCEPTION: {e}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_groq_api()
