import re
from urllib.parse import urlparse
from typing import Dict, List, Tuple, Union

VALID_SCHEMES = {"http", "https"}
SUSPICIOUS_KEYWORDS = {
    "login",
    "verify",
    "update",
    "secure",
    "banking",
    "password",
    "credential",
}


def normalize_url(raw_url: str) -> str:
    """Ensure the URL has a scheme so urlparse works consistently."""
    raw_url = raw_url.strip()
    if not raw_url:
        return raw_url

    parsed = urlparse(raw_url)
    if not parsed.scheme:
        raw_url = f"http://{raw_url}"
    return raw_url


def is_valid_url(raw_url: str) -> bool:
    """Return True when the supplied string looks like a URL we can analyze."""
    if not raw_url:
        return False
    parsed = urlparse(normalize_url(raw_url))
    return bool(parsed.scheme in VALID_SCHEMES and parsed.netloc)


def keyword_flags(host: str) -> List[str]:
    lowered = host.lower()
    return [kw for kw in SUSPICIOUS_KEYWORDS if kw in lowered]


def heuristics_score(features: Dict[str, Union[float, int, bool]]) -> Tuple[float, List[str]]:
    """Lightweight heuristic scoring to complement the LLM verdict.
    Returns a score from 0.0 (legitimate) to 0.95 (highly suspicious).
    Legitimate URLs should score close to 0.0 for ~100% confidence.
    """
    score = 0.0
    reasons: list[str] = []

    # High-confidence phishing indicators (these alone can push score over 0.5)
    if features.get("has_at_in_host"):
        score += 0.4
        reasons.append("URL contains '@' in the host, which can hide the real destination domain (common phishing technique).")

    if features.get("typosquatting_detected"):
        score += 0.35
        reasons.append("URL appears to be a typosquatting attempt (misspelled brand name).")

    if features.get("shortener_domain"):
        score += 0.3
        reasons.append("URL uses a known URL shortener, which is common in phishing links to hide destination.")
    
    # NEW: Suspicious keywords in path (login, account, verify, etc) - HIGH indicator
    if features.get("has_suspicious_path"):
        score += 0.35
        reasons.append("URL path contains suspicious keywords (login, account, verify, etc.) commonly used in phishing.")
    
    # NEW: Brand names embedded in unusual locations
    if features.get("has_embedded_brand"):
        score += 0.25
        reasons.append("Brand name (PayPal, Amazon, etc.) found embedded in unusual location in URL path.")
    
    # NEW: CMS hosting paths commonly abused for phishing
    if features.get("has_cms_path"):
        score += 0.2
        reasons.append("URL path suggests content is hosted on compromised website (WordPress, Joomla, etc.).")
    
    # If both @ and shortener are present, it's a very strong phishing signal
    if features.get("has_at_in_host") and features.get("shortener_domain"):
        score += 0.15
        reasons.append("Combination of '@' obfuscation and URL shortener is highly suspicious.")

    # Medium-confidence indicators
    if features.get("uses_ip_address"):
        score += 0.2
        reasons.append("URL uses raw IP address instead of domain.")

    if features.get("suspicious_keyword_matches", 0):
        score += 0.2
        reasons.append("Contains keywords commonly used in phishing lures.")

    if features.get("num_subdomains", 0) >= 3:  # Increased threshold to avoid false positives
        score += 0.15
        reasons.append("URL contains an unusually deep subdomain chain.")

    if features.get("url_length", 0) > 100:  # Increased threshold
        score += 0.15
        reasons.append("URL length exceeds 100 characters.")

    # Lower-confidence indicators (only add if already suspicious)
    if score > 0.2:  # Only apply these if we already have some suspicion
        if not features.get("uses_https", True):
            score += 0.1
            reasons.append("Connection is not secured with HTTPS.")

        if features.get("count_special_chars", 0) > 5:  # Increased threshold
            score += 0.1
            reasons.append("Too many special characters often used to obfuscate.")

        if features.get("count_digits", 0) > 10:  # Increased threshold
            score += 0.1
            reasons.append("Contains unusually high digit counts in the URL.")

        if features.get("query_length", 0) > 30:  # Increased threshold
            score += 0.05
            reasons.append("Very long query string resembles tracking/obfuscation.")

        if features.get("has_mismatched_tld"):
            score += 0.1
            reasons.append("Uncommon TLD for the organization name.")

    score = min(score, 0.95)
    return round(score, 2), reasons


def build_prompt(url: str, features: Dict[str, Union[float, int, bool, str]]) -> str:
    """Create a compact prompt for whatever LLM provider is configured."""
    lines = [
        "You are a cybersecurity assistant that analyzes URLs for phishing attempts.",
        "Analyze the following URL and respond ONLY with valid JSON in this exact format:",
        '{"verdict": "phishing" or "legitimate", "confidence": 0.0-1.0, "explanation": "brief explanation", "reasons": ["reason1", "reason2"]}',
        "",
        f"URL to analyze: {url}",
        f"Extracted features: {features}",
        "",
        "IMPORTANT: Respond with ONLY the JSON object, no additional text before or after.",
    ]
    return "\n".join(lines)


def dedupe_reasons(*reason_lists: List[str]) -> List[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for reasons in reason_lists:
        for reason in reasons:
            if reason and reason not in seen:
                ordered.append(reason)
                seen.add(reason)
    return ordered

