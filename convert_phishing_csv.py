"""
Special converter for phishing_site_urls.csv that adds http:// to URLs without schemes.
"""

import json
import csv
from pathlib import Path
from typing import List, Tuple

def load_phishing_urls(file_path: str) -> List[Tuple[str, str]]:
    """Load URLs from CSV and add http:// if missing."""
    urls = []
    
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader):
            if i % 50000 == 0:
                print(f"  Processing row {i}...", end="\r")
            
            url = row.get("URL", "").strip()
            label = row.get("Label", "bad").lower().strip()
            
            if not url:
                continue
            
            # Add http:// if URL doesn't have a scheme
            if not url.startswith(("http://", "https://", "ftp://")):
                url = "http://" + url
            
            # Map label: "bad" = phishing, others = legitimate
            url_label = "phishing" if label in ("bad", "phishing", "malicious") else "legitimate"
            
            urls.append((url, url_label))
    
    print(f"  Processing complete!      ")
    return urls

def save_json(urls: List[Tuple[str, str]], output_file: str):
    """Save to JSON format."""
    data = [{"url": url, "label": label} for url, label in urls]
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✅ Saved {len(urls)} URLs to {output_file}")

def print_stats(urls: List[Tuple[str, str]]):
    """Print dataset statistics."""
    phishing = sum(1 for _, label in urls if label == "phishing")
    legitimate = sum(1 for _, label in urls if label == "legitimate")
    
    print(f"\n📊 Dataset Statistics:")
    print(f"  Total URLs:    {len(urls):,}")
    print(f"  Phishing:      {phishing:,} ({phishing/len(urls)*100:.1f}%)")
    print(f"  Legitimate:    {legitimate:,} ({legitimate/len(urls)*100:.1f}%)")
    
    print(f"\n📋 Sample URLs (first 5):")
    for url, label in urls[:5]:
        print(f"  • {url[:65]:65} [{label}]")

if __name__ == "__main__":
    import sys
    
    print("🔄 Converting phishing_site_urls.csv...\n")
    print("📂 Loading URLs...\n")
    
    urls = load_phishing_urls("phishing_site_urls.csv")
    save_json(urls, "my_phishing_dataset.json")
    print_stats(urls)
