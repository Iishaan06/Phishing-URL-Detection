"""Test script to diagnose LLM provider errors."""
import os
import sys
import json
import requests

# Set up environment
# API key - Set via environment variable LLM_API_KEY
api_key = os.getenv("LLM_API_KEY")
base_url = os.getenv("LLM_BASE_URL", "https://api.perplexity.ai/chat/completions")
# Version - Model version/name
model = os.getenv("LLM_MODEL", "sonar-pro")
# Provider - LLM provider name
provider = os.getenv("LLM_PROVIDER", "perplexity")

if not api_key:
    print("❌ LLM_API_KEY not set!")
    sys.exit(1)

print("Testing LLM with a simple URL analysis...")
print(f"Base URL: {base_url}")
print(f"Model: {model}")
print()

# Test with a simple prompt similar to what the app uses
prompt = """You are a cybersecurity assistant that analyzes URLs for phishing attempts.
Analyze the following URL and respond ONLY with valid JSON in this exact format:
{"verdict": "phishing" or "legitimate", "confidence": 0.0-1.0, "explanation": "brief explanation", "reasons": ["reason1", "reason2"]}

URL to analyze: https://www.facebook.com
Extracted features: {'normalized_url': 'https://www.facebook.com', 'url_length': 25, 'uses_https': True}

IMPORTANT: Respond with ONLY the JSON object, no additional text before or after."""

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

payload = {
    "model": model,
    "messages": [
        {"role": "user", "content": prompt}
    ],
    "temperature": 0.0,
}

try:
    print("Sending request...")
    response = requests.post(base_url, headers=headers, json=payload, timeout=15)
    
    print(f"Status Code: {response.status_code}")
    print()
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Request successful!")
        print()
        print("Full response:")
        print(json.dumps(data, indent=2))
        print()
        
        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0].get("message", {}).get("content", "")
            print("Response content:")
            print(content)
            print()
            
            # Try to parse as JSON
            try:
                parsed = json.loads(content)
                print("✅ Successfully parsed as JSON:")
                print(json.dumps(parsed, indent=2))
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse as JSON: {e}")
                print("The response is not valid JSON. This is the issue!")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Exception: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

