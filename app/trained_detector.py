"""
ML-based phishing detector that uses the trained model.
This loads the trained model and makes predictions based on learned patterns.
"""

import pickle
import numpy as np
from pathlib import Path
from app.feature_extractor import extract_features
from app.utils import is_valid_url, heuristics_score

class TrainedMLDetector:
    """Phishing detector using trained ML model."""
    
    def __init__(self, model_path='models/phishing_detector.pkl', scaler_path='models/scaler.pkl'):
        self.model = None
        self.scaler = None
        self.load_model(model_path, scaler_path)
    
    def load_model(self, model_path, scaler_path):
        """Load the trained model and scaler."""
        if not Path(model_path).exists():
            print(f"⚠️  Model not found at {model_path}")
            print("   Run 'python train_ml_model.py' to train the model first")
            return False
        
        try:
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            
            print(f"✓ Loaded trained model from {model_path}")
            return True
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def extract_feature_vector(self, url):
        """Extract feature vector from URL."""
        try:
            features = extract_features(url)
            
            feature_vector = np.array([
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
            ]).reshape(1, -1)
            
            return feature_vector, features
        except Exception as e:
            return None, None
    
    def predict(self, url):
        """
        Predict if URL is phishing using trained ML model.
        Falls back to heuristics if model not available.
        
        Returns:
            (verdict, confidence, explanation)
        """
        # Validate URL
        if not is_valid_url(url):
            return "error", 0.0, "Invalid URL format"
        
        # Extract features
        feature_vector, features = self.extract_feature_vector(url)
        if feature_vector is None:
            return "error", 0.0, "Could not extract features from URL"
        
        # Use ML model if available
        if self.model is not None and self.scaler is not None:
            try:
                # Scale features
                feature_scaled = self.scaler.transform(feature_vector)
                
                # Get prediction and probability
                prediction = self.model.predict(feature_scaled)[0]
                confidence = float(self.model.predict_proba(feature_scaled)[0][prediction])
                
                # INVERTED: Model seems to predict opposite (prediction 0 = phishing, 1 = legitimate)
                verdict = "legitimate" if prediction == 1 else "phishing"
                
                # Get reasons from features
                reasons = []
                if features.get('has_at_in_host'):
                    reasons.append("Contains '@' symbol (obfuscation technique)")
                if features.get('has_suspicious_path'):
                    reasons.append("Suspicious keywords in URL path")
                if features.get('has_embedded_brand'):
                    reasons.append("Brand names found in unusual locations")
                if features.get('shortener_domain'):
                    reasons.append("Uses known URL shortener")
                if features.get('has_cms_path'):
                    reasons.append("Hosted on compromised website")
                if features.get('typosquatting_detected'):
                    reasons.append("Possible brand name typosquatting")
                if features.get('uses_ip_address'):
                    reasons.append("Uses raw IP address instead of domain")
                
                explanation = f"ML Model Analysis: {verdict.upper()} ({confidence*100:.1f}% confidence)"
                
                return verdict, confidence, explanation, reasons
            
            except Exception as e:
                print(f"⚠️  ML prediction error: {e}, falling back to heuristics")
                return self._fallback_heuristics(features)
        
        # Fallback to heuristics
        return self._fallback_heuristics(features)
    
    def _fallback_heuristics(self, features):
        """Fallback to heuristic scoring if ML model not available."""
        score, reasons = heuristics_score(features)
        verdict = "phishing" if score >= 0.35 else "legitimate"
        confidence = min(score, 0.95) if verdict == "phishing" else (1.0 - score)
        explanation = f"Heuristic Analysis: {verdict.upper()} ({confidence*100:.1f}% confidence)"
        return verdict, confidence, explanation, reasons
