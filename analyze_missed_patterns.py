"""
Analyze missed phishing URLs to find common patterns
"""

import json
from app.feature_extractor import extract_features
from collections import defaultdict

# Load missed phishing URLs
data = json.load(open('my_phishing_dataset.json'))
detector_score_zero = []

for item in data:
    if item['label'] == 'phishing':
        try:
            features = extract_features(item['url'])
            score = 0.0
            
            # Simulate heuristics
            if features.get("has_at_in_host"):
                score += 0.4
            if features.get("typosquatting_detected"):
                score += 0.35
            if features.get("shortener_domain"):
                score += 0.3
            
            score = min(score, 0.95)
            
            # Find URLs that score 0
            if score < 0.35:  # Below detection threshold
                detector_score_zero.append(item['url'])
        except:
            pass

print(f"Found {len(detector_score_zero)} phishing URLs with low scores\n")

# Analyze patterns
print("Sample missed phishing URLs:")
for url in detector_score_zero[:20]:
    print(f"  • {url[:80]}")

# Analyze common features
print("\n\nCommon patterns in missed phishing:")

# Check for suspicious keywords
suspicious_keywords = {
    "verify": 0, "confirm": 0, "update": 0, "secure": 0,
    "action": 0, "urgent": 0, "alert": 0, "account": 0,
    "login": 0, "banking": 0, "payment": 0, "card": 0,
    "password": 0, "validate": 0, "authorize": 0, "details": 0
}

domain_keyword_count = 0
uri_keyword_count = 0

for url in detector_score_zero[:3000]:  # Sample
    url_lower = url.lower()
    # Check path and query
    if '/' in url:
        parts = url.split('/', 3)
        if len(parts) > 3:
            path = parts[3]
            for kw in suspicious_keywords:
                if kw in path:
                    suspicious_keywords[kw] += 1
                    uri_keyword_count += 1

print("Suspicious keywords in URL paths:")
sorted_kw = sorted(suspicious_keywords.items(), key=lambda x: x[1], reverse=True)
for kw, count in sorted_kw[:10]:
    if count > 0:
        print(f"  • '{kw}': {count} URLs")

# Check for other patterns
print("\n\nOther patterns:")

# Check for sites that look like they host phishing pages (wordpress, joomla, etc)
wordpress_count = sum(1 for u in detector_score_zero[:5000] if '/wp-' in u or '/wordpress' in u)
joomla_count = sum(1 for u in detector_score_zero[:5000] if '/joomla' in u or '/components/' in u)
unusual_tld = sum(1 for u in detector_score_zero[:5000] if u.endswith(('.tk', '.ga', '.ml', '.cf', '.gq', '.info', '.xyz')))

print(f"  WordPress hosting paths: {wordpress_count}")
print(f"  Joomla hosting paths: {joomla_count}")
print(f"  Unusual TLDs (.tk, .ga, .ml, etc): {unusual_tld}")
