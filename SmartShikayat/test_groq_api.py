"""
Test script to verify Groq API connectivity and model availability
"""
import requests
import os
import sys

# Add parent directory to path to import Django settings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartShikayat.settings')

import django
django.setup()

from django.conf import settings

def test_groq_api():
    """Test Groq API with a simple text request"""
    print("=" * 60)
    print("Testing Groq API Connection")
    print("=" * 60)
    
    api_key = settings.GROQ_API_KEY
    print(f"\n1. API Key: {api_key[:20]}...{api_key[-10:]}")
    
    # Test 1: List available models
    print("\n2. Testing API endpoint - Listing models...")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers=headers
        )
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            models = response.json()
            print(f"   ✓ API is accessible!")
            print(f"\n3. Available vision models:")
            
            vision_models = [m for m in models.get('data', []) if 'vision' in m.get('id', '').lower()]
            if vision_models:
                for model in vision_models:
                    print(f"   - {model['id']}")
            else:
                print("   No vision models found in the list")
                print("\n   All available models:")
                for model in models.get('data', [])[:10]:  # Show first 10
                    print(f"   - {model['id']}")
        else:
            print(f"   ✗ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: Try a simple vision request
    print("\n4. Testing vision model with a simple request...")
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    # Create a simple test payload (without image for now)
    payload = {
        "model": "llama-3.2-11b-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": "Hello, can you see images?"
            }
        ],
        "temperature": 0.1,
        "max_tokens": 50
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Model is accessible!")
            print(f"   Response: {result['choices'][0]['message']['content']}")
        else:
            print(f"   ✗ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    test_groq_api()
