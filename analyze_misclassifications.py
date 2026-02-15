"""
Fine-tune the phishing detector by adjusting scoring thresholds and rules
based on your specific dataset.

This tool analyzes misclassifications and suggests threshold adjustments.
"""

import json
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass

from app.feature_extractor import extract_features
from app.utils import heuristics_score, is_valid_url


@dataclass
class URLAnalysis:
    url: str
    true_label: str
    predicted_label: str
    heuristic_score: float
    features: Dict
    was_correct: bool


class MisclassificationAnalyzer:
    def __init__(self, dataset_file: str):
        self.dataset_file = Path(dataset_file)
        self.analyses: List[URLAnalysis] = []
        self.false_positives: List[URLAnalysis] = []  # Legitimate but flagged as phishing
        self.false_negatives: List[URLAnalysis] = []  # Phishing but flagged as legitimate

    def load_and_analyze(self):
        """Load dataset and identify misclassifications."""
        dataset = self._load_dataset()
        
        for url, true_label in dataset:
            if not is_valid_url(url):
                continue
            
            features = extract_features(url)
            score, _ = heuristics_score(features)
            predicted_label = "phishing" if score >= 0.5 else "legitimate"
            was_correct = predicted_label == true_label
            
            analysis = URLAnalysis(
                url=url,
                true_label=true_label,
                predicted_label=predicted_label,
                heuristic_score=score,
                features=features,
                was_correct=was_correct
            )
            self.analyses.append(analysis)
            
            if not was_correct:
                if predicted_label == "phishing" and true_label == "legitimate":
                    self.false_positives.append(analysis)
                elif predicted_label == "legitimate" and true_label == "phishing":
                    self.false_negatives.append(analysis)

    def _load_dataset(self) -> List[Tuple[str, str]]:
        """Load dataset (supports JSON, CSV, TXT)."""
        urls = []
        
        if self.dataset_file.suffix == ".json":
            with open(self.dataset_file, "r") as f:
                data = json.load(f)
                for item in data:
                    urls.append((item["url"], item["label"]))
        elif self.dataset_file.suffix == ".csv":
            import csv
            with open(self.dataset_file, "r") as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if len(row) >= 2:
                        urls.append((row[0].strip(), row[1].lower().strip()))
        
        return urls

    def print_report(self):
        """Print detailed analysis of misclassifications."""
        total = len(self.analyses)
        correct = sum(1 for a in self.analyses if a.was_correct)
        accuracy = correct / total if total > 0 else 0
        
        print(f"\n{'='*70}")
        print(f"  Misclassification Analysis Report")
        print(f"{'='*70}\n")
        
        print(f"Overall Accuracy: {accuracy:.1%} ({correct}/{total} correct)\n")
        
        # Analyze false positives (legitimate URLs wrongly flagged as phishing)
        if self.false_positives:
            print(f"❌ FALSE POSITIVES: {len(self.false_positives)} legitimate URLs flagged as phishing\n")
            self._print_pattern_analysis(self.false_positives)
            print()
        
        # Analyze false negatives (phishing URLs missed)
        if self.false_negatives:
            print(f"❌ FALSE NEGATIVES: {len(self.false_negatives)} phishing URLs not detected\n")
            self._print_pattern_analysis(self.false_negatives)
            print()
        
        print(f"{'='*70}\n")

    def _print_pattern_analysis(self, misclassifications: List[URLAnalysis]):
        """Analyze common features in misclassified URLs."""
        
        print("Top URLs:")
        for analysis in misclassifications[:5]:
            print(f"  • {analysis.url[:65]}")
            print(f"    Score: {analysis.heuristic_score:.2f} | Features: {self._feature_summary(analysis)}")
        
        if len(misclassifications) > 5:
            print(f"  ... and {len(misclassifications) - 5} more\n")
        
        # Feature statistics
        feature_stats = self._analyze_features(misclassifications)
        
        print("\nCommon Features in Misclassifications:")
        for feature, pct in sorted(feature_stats.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  • {feature}: {pct:.1%}")

    def _feature_summary(self, analysis: URLAnalysis) -> str:
        """Create a one-line summary of key features."""
        features = analysis.features
        summary = []
        
        if features.get("has_at_in_host"):
            summary.append("@ in host")
        if features.get("shortener_domain"):
            summary.append("shortener")
        if features.get("typosquatting_detected"):
            summary.append("typo")
        if features.get("uses_ip_address"):
            summary.append("IP addr")
        if features.get("num_subdomains", 0) > 3:
            summary.append(f"{features['num_subdomains']} subdomains")
        
        return " + ".join(summary) if summary else "no flags"

    def _analyze_features(self, misclassifications: List[URLAnalysis]) -> Dict[str, float]:
        """Calculate what % of misclassifications have each feature."""
        feature_counts = {}
        total = len(misclassifications)
        
        for analysis in misclassifications:
            features = analysis.features
            
            if features.get("has_at_in_host"):
                feature_counts["has_at_in_host"] = feature_counts.get("has_at_in_host", 0) + 1
            if features.get("shortener_domain"):
                feature_counts["shortener_domain"] = feature_counts.get("shortener_domain", 0) + 1
            if features.get("typosquatting_detected"):
                feature_counts["typosquatting_detected"] = feature_counts.get("typosquatting_detected", 0) + 1
            if features.get("uses_ip_address"):
                feature_counts["uses_ip_address"] = feature_counts.get("uses_ip_address", 0) + 1
            if features.get("num_subdomains", 0) > 3:
                feature_counts["many_subdomains"] = feature_counts.get("many_subdomains", 0) + 1
            if features.get("url_length", 0) > 100:
                feature_counts["long_url"] = feature_counts.get("long_url", 0) + 1
        
        # Convert to percentages
        return {k: v / total for k, v in feature_counts.items()}


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze misclassifications in your dataset")
    parser.add_argument("--dataset", type=str, required=True, help="Path to dataset file")
    
    args = parser.parse_args()
    
    print(f"\n📊 Analyzing misclassifications in {args.dataset}...\n")
    
    analyzer = MisclassificationAnalyzer(args.dataset)
    analyzer.load_and_analyze()
    analyzer.print_report()


if __name__ == "__main__":
    main()
