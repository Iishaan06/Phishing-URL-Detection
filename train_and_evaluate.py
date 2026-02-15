"""
Train and evaluate the phishing URL detector on your dataset.

Supports dataset formats:
- JSON: [{"url": "...", "label": "phishing|legitimate"}, ...]
- CSV: url,label
- TXT: One URL per line (use header for labels or simple URL list for inference)
"""

import json
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict

from app.feature_extractor import extract_features
from app.utils import heuristics_score, is_valid_url


class PhishingDataset:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.urls: List[Tuple[str, str]] = []  # (url, label)
        self.load()

    def load(self):
        """Load dataset from JSON, CSV, or TXT files."""
        if self.file_path.suffix == ".json":
            self._load_json()
        elif self.file_path.suffix == ".csv":
            self._load_csv()
        elif self.file_path.suffix == ".txt":
            self._load_txt()
        else:
            raise ValueError(f"Unsupported file format: {self.file_path.suffix}")
        
        print(f"✓ Loaded {len(self.urls)} URLs from {self.file_path.name}")

    def _load_json(self):
        """Load from JSON: [{"url": "...", "label": "phishing|legitimate"}, ...]"""
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                url = item.get("url", "").strip()
                label = item.get("label", "").lower().strip()
                if url and label in ("phishing", "legitimate"):
                    self.urls.append((url, label))

    def _load_csv(self):
        """Load from CSV: url,label"""
        with open(self.file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            for row in reader:
                if len(row) >= 2:
                    url = row[0].strip()
                    label = row[1].lower().strip()
                    if url and label in ("phishing", "legitimate"):
                        self.urls.append((url, label))

    def _load_txt(self):
        """Load from TXT: one URL per line"""
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Try to extract label from end of line (e.g., "http://evil.com phishing")
                    parts = line.rsplit(" ", 1)
                    url = parts[0]
                    label = parts[1].lower() if len(parts) > 1 and parts[1] in ("phishing", "legitimate") else None
                    if url and label:
                        self.urls.append((url, label))

    def split(self, train_ratio: float = 0.8) -> Tuple["PhishingDataset", "PhishingDataset"]:
        """Split dataset into train/test sets (randomly shuffled)."""
        import random
        shuffled = self.urls.copy()
        random.shuffle(shuffled)
        
        split_idx = int(len(shuffled) * train_ratio)
        train_dataset = PhishingDataset.__new__(PhishingDataset)
        train_dataset.urls = shuffled[:split_idx]
        
        test_dataset = PhishingDataset.__new__(PhishingDataset)
        test_dataset.urls = shuffled[split_idx:]
        
        return train_dataset, test_dataset


class PhishingDetector:
    def __init__(self):
        pass

    def predict(self, url: str) -> Tuple[str, float]:
        """
        Predict if URL is phishing or legitimate.
        
        Returns:
            (verdict, confidence) - verdict is "phishing" or "legitimate"
        """
        try:
            if not is_valid_url(url):
                return "unknown", 0.0
            
            features = extract_features(url)
            score, _ = heuristics_score(features)
            
            verdict = "phishing" if score >= 0.35 else "legitimate"
            confidence = min(score, 0.95) if verdict == "phishing" else (1.0 - score)
            
            return verdict, round(confidence, 2)
        except Exception as e:
            # Handle malformed URLs
            return "unknown", 0.0


def evaluate(detector: PhishingDetector, dataset: PhishingDataset) -> Dict:
    """
    Evaluate detector on dataset and return metrics.
    
    Returns:
        {
            "accuracy": float,
            "precision_phishing": float,
            "recall_phishing": float,
            "f1_phishing": float,
            "confusion_matrix": {"TP": int, "FP": int, "TN": int, "FN": int},
            "per_label_stats": {...}
        }
    """
    results = {
        "TP": 0, "FP": 0, "TN": 0, "FN": 0,
        "phishing_urls": [],
        "legitimate_urls": []
    }

    for url, true_label in dataset.urls:
        pred_verdict, confidence = detector.predict(url)
        
        # Skip invalid/unknown URLs
        if pred_verdict == "unknown":
            continue
        
        if true_label == "phishing":
            if pred_verdict == "phishing":
                results["TP"] += 1
            else:
                results["FN"] += 1
                results["phishing_urls"].append((url, confidence, "MISSED"))
        else:  # legitimate
            if pred_verdict == "legitimate":
                results["TN"] += 1
            else:
                results["FP"] += 1
                results["legitimate_urls"].append((url, confidence, "FALSE_ALARM"))

    # Calculate metrics
    total = len(dataset.urls)
    tp, fp, tn, fn = results["TP"], results["FP"], results["TN"], results["FN"]
    
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "accuracy": round(accuracy, 3),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1_score": round(f1, 3),
        "confusion_matrix": {
            "TP": tp, "FP": fp, "TN": tn, "FN": fn
        },
        "split_stats": {
            "total_urls": total,
            "phishing": sum(1 for _, label in dataset.urls if label == "phishing"),
            "legitimate": sum(1 for _, label in dataset.urls if label == "legitimate")
        },
        "missed_phishing": results["phishing_urls"][:10],  # Show first 10
        "false_alarms": results["legitimate_urls"][:10]
    }


def print_report(metrics: Dict, dataset_name: str = "Dataset"):
    """Pretty-print evaluation metrics."""
    print(f"\n{'='*60}")
    print(f"  {dataset_name} Evaluation Results")
    print(f"{'='*60}\n")
    
    cm = metrics["confusion_matrix"]
    split = metrics["split_stats"]
    
    print(f"Dataset Size:        {split['total_urls']} URLs")
    print(f"  ├─ Phishing:       {split['phishing']}")
    print(f"  └─ Legitimate:     {split['legitimate']}\n")
    
    print(f"Confusion Matrix:")
    print(f"  TP (Correct Phishing):    {cm['TP']}")
    print(f"  TN (Correct Legitimate):  {cm['TN']}")
    print(f"  FP (False Alarms):        {cm['FP']}")
    print(f"  FN (Missed Phishing):     {cm['FN']}\n")
    
    print(f"Metrics:")
    print(f"  Accuracy:    {metrics['accuracy']:.1%}")
    print(f"  Precision:   {metrics['precision']:.1%}")
    print(f"  Recall:      {metrics['recall']:.1%}")
    print(f"  F1-Score:    {metrics['f1_score']:.1%}\n")
    
    if metrics['missed_phishing']:
        print(f"⚠️  Missed Phishing URLs (showing first 10):")
        for url, conf, _ in metrics['missed_phishing']:
            print(f"    • {url[:70]} (confidence: {conf})")
    
    if metrics['false_alarms']:
        print(f"\n⚠️  False Alarms (showing first 10):")
        for url, conf, _ in metrics['false_alarms']:
            print(f"    • {url[:70]} (confidence: {conf})")
    
    print(f"\n{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Train and evaluate the phishing URL detector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python train_and_evaluate.py --dataset my_urls.json
  python train_and_evaluate.py --dataset phishing_data.csv --split 0.8
  python train_and_evaluate.py --dataset urls.txt
        """
    )
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="Path to dataset file (JSON, CSV, or TXT)"
    )
    parser.add_argument(
        "--split",
        type=float,
        default=0.8,
        help="Train/test split ratio (default: 0.8)"
    )
    parser.add_argument(
        "--evaluate-only",
        action="store_true",
        help="Evaluate on full dataset without splitting"
    )
    
    args = parser.parse_args()
    
    # Load dataset
    print(f"\n📂 Loading dataset from {args.dataset}...")
    try:
        dataset = PhishingDataset(args.dataset)
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        return
    
    # Initialize detector
    detector = PhishingDetector()
    
    if args.evaluate_only:
        # Evaluate on full dataset
        print("\n🧪 Evaluating on full dataset...\n")
        metrics = evaluate(detector, dataset)
        print_report(metrics, "Full Dataset")
    else:
        # Split into train/test
        train_dataset, test_dataset = dataset.split(args.split)
        
        print(f"\n📊 Split: {len(train_dataset.urls)} training, {len(test_dataset.urls)} test\n")
        
        # Evaluate on test set
        print("🧪 Evaluating on test set...\n")
        test_metrics = evaluate(detector, test_dataset)
        print_report(test_metrics, "Test Set")
        
        # Also show training set metrics
        print("📈 Evaluating on training set (for reference)...\n")
        train_metrics = evaluate(detector, train_dataset)
        print_report(train_metrics, "Training Set")


if __name__ == "__main__":
    main()
