"""
Improved model training with better data cleaning and hyperparameters.
This version filters out corrupted URLs and tunes the model for better phishing detection.
"""

import json
import pickle
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from app.feature_extractor import extract_features
from app.utils import is_valid_url

def is_clean_url(url):
    """Check if URL is properly formatted (not corrupted)."""
    # Filter out URLs with too many special characters or encoding issues
    special_chars = sum(1 for c in url if ord(c) > 127)  # Non-ASCII characters
    if special_chars > url.count('/'):  # Too many weird characters
        return False
    return True

def load_and_clean_dataset(file_path):
    """Load dataset and clean corrupted URLs."""
    print("📂 Loading dataset from", file_path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"   Initial dataset: {len(data)} URLs")
    
    # Filter out corrupted URLs
    clean_data = [item for item in data if is_clean_url(item['url'])]
    removed = len(data) - len(clean_data)
    
    print(f"   After cleaning: {len(clean_data)} URLs (removed {removed} corrupted)")
    
    return clean_data

def extract_features_batch(data):
    """Extract features from all URLs."""
    print("\n🔍 Extracting features from URLs...")
    
    X = []
    y = []
    skipped = 0
    count = 0
    
    for item in data:
        url = item['url']
        label = item['label']
        
        # Skip invalid URLs
        try:
            if not is_valid_url(url):
                skipped += 1
                continue
        except:
            skipped += 1
            continue
        
        try:
            features = extract_features(url)
            
            # Convert features to numeric vector
            feature_vector = [
                features.get('url_length', 0),
                features.get('num_dots', 0),
                features.get('num_subdomains', 0),
                features.get('count_digits', 0),
                features.get('count_special_chars', 0),
                float(features.get('has_at_in_host', False)),
                float(features.get('shortener_domain', False)),
                float(features.get('typosquatting_detected', False)),
                float(features.get('uses_ip_address', False)),
                float(features.get('has_suspicious_path', False)),
                float(features.get('has_embedded_brand', False)),
                float(features.get('has_cms_path', False)),
                features.get('suspicious_path_keywords', 0),
                features.get('path_length', 0),
                features.get('query_length', 0),
                float(features.get('uses_https', True)),
                float(features.get('has_mismatched_tld', False)),
                features.get('suspicious_keyword_matches', 0),
            ]
            
            X.append(feature_vector)
            # Convert label to binary: 1 = phishing, 0 = legitimate
            y.append(1 if label in ('phishing', 'bad', 'malicious') else 0)
            count += 1
            
            if count % 50000 == 0:
                print(f"  Processed {count:,} URLs...", end='\r')
        
        except Exception as e:
            skipped += 1
            continue
    
    print(f"\n✓ Extracted {len(X):,} feature vectors (skipped {skipped:,} invalid URLs)")
    
    # Print dataset breakdown
    phishing_count = sum(y)
    legit_count = len(y) - phishing_count
    print(f"\nDataset breakdown:")
    print(f"  Legitimate URLs: {legit_count:,}")
    print(f"  Phishing URLs:   {phishing_count:,}")
    print(f"  Total:           {len(X):,}")
    
    return np.array(X), np.array(y)

def train_improved_model(X, y):
    """Train improved Random Forest with better hyperparameters."""
    print("\n🤖 Training improved Random Forest model...")
    
    # Split data: 80% train, 20% test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    print("  Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train with optimized hyperparameters
    # Increased depth to capture more complex patterns
    # Increased trees for better generalization
    print("  Training Random Forest (this may take 2-3 minutes)...")
    model = RandomForestClassifier(
        n_estimators=200,        # More trees
        max_depth=20,            # Deeper trees
        min_samples_split=5,     # More sensitive to splits
        min_samples_leaf=2,      # More granular leaves
        class_weight='balanced', # Handle class imbalance
        random_state=42,
        n_jobs=-1                # Use all CPU cores
    )
    
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    print("\n📊 Evaluating model on test set...")
    y_pred = model.predict(X_test_scaled)
    
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    print(f"  Accuracy:  {accuracy:.3f}")
    print(f"  Precision: {precision:.3f}")
    print(f"  Recall:    {recall:.3f} (IMPORTANT: catches more phishing)")
    print(f"  F1-Score:  {f1:.3f}")
    
    return model, scaler

def save_model(model, scaler, model_path='models/phishing_detector.pkl', scaler_path='models/scaler.pkl'):
    """Save model and scaler."""
    print(f"\n💾 Saving model to {model_path}...")
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"💾 Saving scaler to {scaler_path}...")
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    
    print("✓ Model saved successfully!")

if __name__ == '__main__':
    # Load and clean
    data = load_and_clean_dataset('my_phishing_dataset.json')
    
    # Extract features
    X, y = extract_features_batch(data)
    
    # Train
    model, scaler = train_improved_model(X, y)
    
    # Save
    save_model(model, scaler)
    
    print("\n✅ Training complete! New model is ready to use.")
    print("Restart Flask server to use the improved model.")
