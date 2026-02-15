"""
Train a Machine Learning model on the phishing dataset.
This model learns patterns from phishing_site_urls.csv and saves the trained model.
"""

import json
import pickle
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import warnings
warnings.filterwarnings('ignore')

from app.feature_extractor import extract_features
from app.utils import is_valid_url

def load_dataset(json_file):
    """Load the phishing dataset."""
    print(f"📂 Loading dataset from {json_file}...")
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data

def extract_feature_vectors(dataset, max_urls=None):
    """Extract feature vectors from URLs for ML training."""
    X = []  # Features
    y = []  # Labels (1 = phishing, 0 = legitimate)
    
    count = 0
    skipped = 0
    for item in dataset:
        if max_urls and count >= max_urls:
            break
            
        url = item.get('url', '').strip()
        label = item.get('label', '').lower()
        
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
            
            if count % 10000 == 0:
                print(f"  Processed {count:,} URLs...", end='\r')
        
        except Exception as e:
            skipped += 1
            continue
    
    print(f"\n✓ Extracted {len(X):,} feature vectors (skipped {skipped:,} invalid URLs)")
    return np.array(X), np.array(y)

def train_model(X, y):
    """Train the ML model."""
    print("\n🤖 Training Random Forest model...")
    
    # Split data: 80% train, 20% test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    print("  Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Random Forest
    print("  Training Random Forest (this may take a minute)...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        random_state=42,
        n_jobs=-1,
        verbose=0
    )
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    print("\n📊 Evaluating model on test set...")
    y_pred = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    
    print(f"\n  Accuracy:  {accuracy:.3f}")
    print(f"  Precision: {precision:.3f}")
    print(f"  Recall:    {recall:.3f}")
    print(f"  F1-Score:  {f1:.3f}")
    
    return model, scaler

def save_model(model, scaler, model_path='models/phishing_detector.pkl', scaler_path='models/scaler.pkl'):
    """Save trained model and scaler."""
    Path('models').mkdir(exist_ok=True)
    
    print(f"\n💾 Saving model to {model_path}...")
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"💾 Saving scaler to {scaler_path}...")
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    
    print("✓ Model saved successfully!")

def main():
    # Load dataset
    dataset = load_dataset('my_phishing_dataset.json')
    
    # Extract features
    print("\n🔍 Extracting features from URLs...")
    X, y = extract_feature_vectors(dataset)
    
    print(f"\nDataset breakdown:")
    print(f"  Legitimate URLs: {np.sum(y == 0):,}")
    print(f"  Phishing URLs:   {np.sum(y == 1):,}")
    print(f"  Total:           {len(y):,}")
    
    # Train model
    model, scaler = train_model(X, y)
    
    # Save model
    save_model(model, scaler)
    
    print("\n✅ Training complete! Model is ready to use.")
    print("\nYour detector will now use the trained ML model for predictions.")

if __name__ == '__main__':
    main()
