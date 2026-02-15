import ipaddress
from urllib.parse import urlparse
from typing import Dict, List, Tuple, Union

from .utils import keyword_flags, normalize_url

COMMON_LEGIT_TLDS = {"com", "org", "net", "edu", "gov", "mil", "io"}
SPECIAL_CHARS = set("@!#$%^&*+=?|~_-")


def _host_components(netloc: str) -> Tuple[str, List[str]]:
    host = netloc.split(":")[0].lower()
    parts = [p for p in host.split(".") if p]
    return host, parts


def _has_mismatched_tld(parts: List[str]) -> bool:
    if not parts:
        return False
    tld = parts[-1]
    return tld not in COMMON_LEGIT_TLDS and len(parts) > 1


def extract_features(raw_url: str) -> Dict[str, Union[int, float, str, bool, List[str]]]:
    """Derive lightweight, explainable features from a URL."""
    normalized_url = normalize_url(raw_url)
    parsed = urlparse(normalized_url)
    host, parts = _host_components(parsed.netloc)

    try:
        ipaddress.ip_address(host)
        uses_ip = True
    except ValueError:
        uses_ip = False

    digits = sum(ch.isdigit() for ch in normalized_url)
    specials = sum(ch in SPECIAL_CHARS for ch in normalized_url)
    subdomains = max(len(parts) - 2, 0)
    keywords = keyword_flags(host + parsed.path)

    # Detect @ in host (common phishing technique to hide real domain)
    has_at_in_host = "@" in parsed.netloc
    
    # Extract parts for typosquatting (before @) and shortener detection (after @)
    domain_before_at = host  # For typosquatting check
    actual_host = host  # For shortener check
    
    if has_at_in_host:
        # Split by @: "faccebook.com@is.gd" -> ["faccebook.com", "is.gd"]
        netloc_parts = parsed.netloc.split("@")
        if len(netloc_parts) >= 2:
            domain_before_at = netloc_parts[0].split(":")[0].lower()  # "faccebook.com"
            actual_host = netloc_parts[-1].split(":")[0].lower()  # "is.gd"
    
    # Some URL shorteners are frequently used in phishing campaigns.
    SHORTENERS = {"is.gd", "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "buff.ly", "rebrand.ly"}
    shortened = actual_host in SHORTENERS or any(short in actual_host for short in SHORTENERS)
    
    # Detect suspicious keywords in URL path (common in phishing)
    PHISHING_KEYWORDS = {"login", "account", "verify", "confirm", "update", "secure", "password", 
                         "auth", "signin", "checkout", "payment", "card", "banking", "alert"}
    path_lower = parsed.path.lower()
    suspicious_path_keywords = sum(1 for kw in PHISHING_KEYWORDS if kw in path_lower)
    has_suspicious_path = suspicious_path_keywords >= 1
    
    # Detect embedded brand names in URL path (e.g., /paypal.com/ in middle of URL)
    MAJOR_BRANDS = ["paypal", "amazon", "google", "facebook", "microsoft", "apple", "linkedin", 
                    "linkedin", "instagram", "netflix", "bank", "chase", "wellsfargo", "itau"]
    embedded_brands = 0
    if parsed.path != "/":
        for brand in MAJOR_BRANDS:
            # Count occurrences of brand name in path/query (not in domain)
            if brand in parsed.path.lower():
                embedded_brands += 1
            if parsed.query and brand in parsed.query.lower():
                embedded_brands += 1
    has_embedded_brand = embedded_brands >= 1
    
    # Detect CMS/hosting paths that commonly host phishing (wp-content, joomla, etc)
    CMS_PATHS = ["/wp-content/", "/wp-admin/", "/plugins/", "/components/", "/includes/", 
                "/cache/", "/libraries/", "/plugins/", "/modules/"]
    has_cms_path = any(cms in parsed.path.lower() for cms in CMS_PATHS)
    
    # Typosquatting detection: check the domain BEFORE @ for brand name typos
    # e.g., "faccebook.com" (before @) should be checked, not "is.gd" (after @)
    domain_parts = domain_before_at.split(".")
    main_domain = ""
    if len(domain_parts) >= 2:
        # Take the second-to-last part (the actual domain name)
        main_domain = domain_parts[-2].lower()  # "faccebook" from "faccebook.com"
    elif len(domain_parts) == 1:
        # Single part domain
        main_domain = domain_parts[0].lower()
    
    BRAND_NAMES = {"facebook", "google", "amazon", "microsoft", "apple", "paypal", "twitter", "instagram", "linkedin", "netflix", "ebay", "yahoo", "bankofamerica", "wellsfargo", "chase"}
    is_typosquat = False
    
    if main_domain:
        for brand in BRAND_NAMES:
            # Check if main_domain is similar to brand but not exact (typo)
            if main_domain == brand:
                # Exact match - this is legitimate, not typosquatting
                is_typosquat = False
                break
            elif abs(len(main_domain) - len(brand)) <= 2:
                # Check if it's a close typo (e.g., "faccebook" vs "facebook")
                # Count character differences
                if len(main_domain) == len(brand):
                    diff_count = sum(1 for a, b in zip(main_domain, brand) if a != b)
                    if diff_count <= 2 and diff_count > 0:
                        is_typosquat = True
                        break
                elif (len(main_domain) >= 3 and len(brand) >= 3 and 
                      (main_domain.startswith(brand[:3]) or brand.startswith(main_domain[:3]))):
                    # Similar start suggests typo
                    is_typosquat = True
                    break

    return {
        "has_suspicious_path": has_suspicious_path,
        "has_embedded_brand": has_embedded_brand,
        "has_cms_path": has_cms_path,
        "suspicious_path_keywords": suspicious_path_keywords,
        "normalized_url": normalized_url,
        "url_length": len(normalized_url),
        "num_dots": normalized_url.count("."),
        "num_subdomains": subdomains,
        "count_digits": digits,
        "count_special_chars": specials,
        "uses_https": parsed.scheme == "https",
        "uses_ip_address": uses_ip,
        "path_length": len(parsed.path),
        "query_length": len(parsed.query),
        "suspicious_keyword_matches": len(keywords),
        "matched_keywords": keywords,
        "has_mismatched_tld": _has_mismatched_tld(parts),
        "shortener_domain": shortened,
        "has_at_in_host": has_at_in_host,
        "typosquatting_detected": is_typosquat,
    }

