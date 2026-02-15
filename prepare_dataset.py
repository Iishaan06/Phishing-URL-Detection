"""
Prepare your phishing dataset by converting from common formats
and optionally combining multiple sources.

Usage:
    python prepare_dataset.py --input phishing_urls.txt --output dataset.json
    python prepare_dataset.py --input phishing.csv --column-url url --column-label is_phishing --output dataset.json
    python prepare_dataset.py --merge file1.json file2.csv file3.txt --output combined.json
"""

import json
import csv
import argparse
from pathlib import Path
from typing import List, Tuple, Dict, Set
from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    """Check if string is a valid URL."""
    try:
        url_obj = urlparse(url.strip())
        return url_obj.scheme in ("http", "https")
    except Exception:
        return False


def load_txt_urls(file_path: Path) -> List[Tuple[str, str]]:
    """
    Load URLs from TXT file.
    Supports formats:
    - https://evil.com
    - https://evil.com phishing
    - https://evil.com legitimate
    """
    urls = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            # Try to split by space to get label
            parts = line.rsplit(" ", 1)
            url = parts[0].strip()
            
            label = None
            if len(parts) > 1:
                potential_label = parts[1].lower().strip()
                if potential_label in ("phishing", "legitimate", "safe", "malicious"):
                    label = "phishing" if potential_label in ("phishing", "malicious") else "legitimate"
                else:
                    # No valid label, use whole line as URL
                    label = None
                    url = line
            
            if is_valid_url(url):
                # Default to phishing if no label provided (assume phishing URL files)
                default_label = "phishing"
                urls.append((url, label or default_label))
    
    return urls


def load_csv_urls(
    file_path: Path,
    url_column: str = "url",
    label_column: str = "label",
    phishing_values: List[str] = None
) -> List[Tuple[str, str]]:
    """
    Load URLs from CSV file.
    
    Args:
        file_path: Path to CSV file
        url_column: Column name containing URLs
        label_column: Column name containing labels
        phishing_values: List of values that indicate phishing (default: ["phishing", "malicious", "1", "true", "bad"])
    """
    if phishing_values is None:
        phishing_values = ["phishing", "malicious", "1", "true", "bad"]
    
    urls = []
    with open(file_path, "r", encoding="utf-8") as f:
        # Try to detect delimiter
        sample = f.read(1024)
        f.seek(0)
        
        delimiter = "," if "," in sample else (";" if ";" in sample else "\t")
        
        reader = csv.DictReader(f, delimiter=delimiter)
        
        # Normalize column names
        if reader.fieldnames is None:
            print(f"Error: Could not read CSV headers from {file_path}")
            return []
        
        # Find matching columns (case-insensitive)
        columns = {name.lower(): name for name in reader.fieldnames}
        url_col = columns.get(url_column.lower())
        label_col = columns.get(label_column.lower())
        
        if not url_col:
            print(f"Error: Column '{url_column}' not found. Available: {list(reader.fieldnames)}")
            return []
        
        for row in reader:
            url = row.get(url_col, "").strip()
            
            if not is_valid_url(url):
                continue
            
            # Determine label
            label = "phishing"  # Default
            if label_col and row.get(label_col):
                val = str(row.get(label_col)).lower().strip()
                if val in phishing_values:
                    label = "phishing"
                else:
                    label = "legitimate"
            
            urls.append((url, label))
    
    return urls


def load_json_urls(file_path: Path) -> List[Tuple[str, str]]:
    """Load URLs from JSON file."""
    urls = []
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    url = item.get("url", "").strip()
                    label = item.get("label", "phishing").lower().strip()
                    if is_valid_url(url) and label in ("phishing", "legitimate"):
                        urls.append((url, label))
                elif isinstance(item, str):
                    if is_valid_url(item):
                        urls.append((item, "phishing"))
    
    return urls


def deduplicate(urls: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """Remove duplicate URLs, preferring 'phishing' label if conflicts."""
    seen: Dict[str, str] = {}
    
    for url, label in urls:
        normalized = url.lower().strip()
        
        if normalized in seen:
            # If we already have this URL with a phishing label, keep it
            if label == "phishing":
                seen[normalized] = "phishing"
        else:
            seen[normalized] = label
    
    return [(url, label) for url, label in seen.items()]


def save_json(urls: List[Tuple[str, str]], output_file: Path):
    """Save URLs to JSON format."""
    data = [
        {"url": url, "label": label}
        for url, label in urls
    ]
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✅ Saved {len(urls)} URLs to {output_file}")


def print_statistics(urls: List[Tuple[str, str]]):
    """Print dataset statistics."""
    phishing_count = sum(1 for _, label in urls if label == "phishing")
    legitimate_count = sum(1 for _, label in urls if label == "legitimate")
    
    print(f"\n📊 Dataset Statistics:")
    print(f"  Total URLs:    {len(urls)}")
    print(f"  Phishing:      {phishing_count} ({phishing_count/len(urls)*100:.1f}%)")
    print(f"  Legitimate:    {legitimate_count} ({legitimate_count/len(urls)*100:.1f}%)")
    
    # Show some examples
    print(f"\n📋 Sample URLs:")
    for url, label in urls[:5]:
        print(f"  • {url[:60]:60} [{label}]")
    if len(urls) > 5:
        print(f"  ... and {len(urls) - 5} more")


def main():
    parser = argparse.ArgumentParser(
        description="Prepare phishing URL dataset from various formats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert TXT to JSON
  python prepare_dataset.py --input phishing_urls.txt --output dataset.json
  
  # Convert CSV with custom columns
  python prepare_dataset.py --input data.csv --column-url "Website" --column-label "Type" --output dataset.json
  
  # Merge multiple files
  python prepare_dataset.py --merge urls1.txt urls2.csv urls3.json --output combined.json
  
  # Dedup and clean
  python prepare_dataset.py --input messy.json --output clean.json --deduplicate
        """
    )
    
    parser.add_argument(
        "--input",
        type=str,
        help="Input file (TXT, CSV, or JSON)"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output file (JSON format)"
    )
    parser.add_argument(
        "--column-url",
        type=str,
        default="url",
        help="CSV column name containing URLs (default: 'url')"
    )
    parser.add_argument(
        "--column-label",
        type=str,
        default="label",
        help="CSV column name containing labels (default: 'label')"
    )
    parser.add_argument(
        "--merge",
        nargs="+",
        help="Merge multiple files instead of --input"
    )
    parser.add_argument(
        "--deduplicate",
        action="store_true",
        help="Remove duplicate URLs"
    )
    
    args = parser.parse_args()
    
    output_file = Path(args.output)
    all_urls: List[Tuple[str, str]] = []
    
    # Load input files
    if args.merge:
        print(f"\n🔀 Merging {len(args.merge)} files...\n")
        for file_path in args.merge:
            path = Path(file_path)
            if not path.exists():
                print(f"⚠️  File not found: {file_path}")
                continue
            
            print(f"  📂 Loading {path.name}...", end=" ")
            
            if path.suffix == ".txt":
                urls = load_txt_urls(path)
            elif path.suffix == ".csv":
                urls = load_csv_urls(path, args.column_url, args.column_label)
            elif path.suffix == ".json":
                urls = load_json_urls(path)
            else:
                print(f"❌ Unknown format: {path.suffix}")
                continue
            
            print(f"({len(urls)} URLs)")
            all_urls.extend(urls)
    
    elif args.input:
        input_file = Path(args.input)
        if not input_file.exists():
            print(f"❌ Input file not found: {args.input}")
            return
        
        print(f"\n📂 Loading {input_file.name}...\n")
        
        if input_file.suffix == ".txt":
            all_urls = load_txt_urls(input_file)
        elif input_file.suffix == ".csv":
            all_urls = load_csv_urls(input_file, args.column_url, args.column_label)
        elif input_file.suffix == ".json":
            all_urls = load_json_urls(input_file)
        else:
            print(f"❌ Unknown format: {input_file.suffix}")
            return
    
    else:
        print("❌ Provide either --input or --merge")
        parser.print_help()
        return
    
    if not all_urls:
        print("❌ No valid URLs found in input file(s)")
        return
    
    # Deduplicate if requested
    if args.deduplicate or args.merge:
        print(f"\n🔍 Deduplicating... ", end="")
        before = len(all_urls)
        all_urls = deduplicate(all_urls)
        print(f"({before} → {len(all_urls)} unique)")
    
    # Save output
    save_json(all_urls, output_file)
    
    # Print stats
    print_statistics(all_urls)
    print()


if __name__ == "__main__":
    main()
