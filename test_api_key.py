"""Quick test script to verify Perplexity API key is working."""
import os
import sys
import json
import requests

# Check environment variables
# API key - Set via environment variable LLM_API_KEY
api_key = os.getenv("LLM_API_KEY")
base_url = os.getenv("LLM_BASE_URL", "https://api.perplexity.ai/chat/completions")
# Version - Model version/name
model = os.getenv("LLM_MODEL", "sonar-pro")
# Provider - LLM provider name
provider = os.getenv("LLM_PROVIDER", "perplexity")

# If API key not in env, allow direct testing (for quick test only)
if not api_key:
    pass

print("=" * 60)
print("Testing Perplexity API Configuration")
print("=" * 60)
print(f"Provider: {provider}")
print(f"Base URL: {base_url}")
print(f"Model: {model}")
print(f"API Key: {'*' * 20 if api_key else 'NOT SET'}")
print()

if not api_key:
    print("❌ ERROR: LLM_API_KEY environment variable is not set!")
    print("\nTo set it, run in PowerShell:")
    print('  setx LLM_API_KEY "your_perplexity_api_key"')
    print("\nThen close and reopen your terminal.")
    sys.exit(1)

if not base_url:
    print("❌ ERROR: LLM_BASE_URL environment variable is not set!")
    print("\nTo set it, run in PowerShell:")
    print('  setx LLM_BASE_URL "https://api.perplexity.ai/chat/completions"')
    sys.exit(1)

# Test API call
print("Testing API connection...")
print()

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

payload = {
    "model": model,
    "messages": [
        {
            "role": "user",
            "content": 'Analyze this URL: https://example.com. Respond with JSON: {"verdict": "legitimate", "confidence": 0.9, "explanation": "Test"}',
        }
    ],
    "temperature": 0.0,
}

try:
    response = requests.post(base_url, headers=headers, json=payload, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    print()
    
    if response.status_code == 200:
        data = response.json()
        print("✅ SUCCESS! API key is working!")
        print()
        print("Response preview:")
        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0].get("message", {}).get("content", "")
            print(content[:200] + "..." if len(content) > 200 else content)
        else:
            print(json.dumps(data, indent=2)[:500])
    elif response.status_code == 401:
        print("❌ ERROR: Authentication failed!")
        print("Your API key is invalid or expired.")
        print("Please check your Perplexity API key.")
    elif response.status_code == 404:
        print("❌ ERROR: Endpoint not found!")
        print(f"Check that your LLM_BASE_URL is correct: {base_url}")
        print("Should be: https://api.perplexity.ai/chat/completions")
    else:
        print(f"❌ ERROR: API returned status {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
except requests.exceptions.Timeout:
    print("❌ ERROR: Request timed out!")
    print("Check your internet connection.")
except requests.exceptions.ConnectionError:
    print("❌ ERROR: Could not connect to API!")
    print("Check your internet connection and the base URL.")
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")

print()
print("=" * 60)

