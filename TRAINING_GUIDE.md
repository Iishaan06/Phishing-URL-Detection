# Guide: Training Your Phishing URL Detector

## 📋 Dataset Format

Your detector can train on datasets in these formats:

### JSON Format (Recommended)
```json
[
  {
    "url": "https://accounts.google.com/signin",
    "label": "legitimate"
  },
  {
    "url": "http://paypal.com.security-updates.info/login",
    "label": "phishing"
  },
  {
    "url": "https://evil-amazon-login.xyz/verify",
    "label": "phishing"
  }
]
```

### CSV Format
```csv
url,label
https://accounts.google.com/signin,legitimate
http://paypal.com.security-updates.info/login,phishing
https://evil-amazon-login.xyz/verify,phishing
```

### TXT Format
```
https://legitimate-bank.com/login legitimate
http://phishing-site.xyz/verify phishing
https://real-store.com/checkout legitimate
```

---

## 🚀 Step-by-Step Training & Evaluation

### Step 1: Prepare Your Dataset

Convert your phishing URL list into one of the supported formats above. Make sure you have:
- ✅ Valid URLs (with http:// or https://)
- ✅ Labels: either "phishing" or "legitimate"
- ✅ Reasonable balance (more phishing URLs = better detection)

**Example:** If you have 1000 phishing URLs, try to get ~500-1000 legitimate URLs for comparison.

### Step 2: Evaluate Current Performance

Test the detector on your dataset to see its baseline accuracy:

```bash
# Activate your virtual environment
.\env\Scripts\Activate.ps1

# Evaluate on full dataset
python train_and_evaluate.py --dataset your_phishing_urls.json

# Or split into 80% train, 20% test
python train_and_evaluate.py --dataset your_phishing_urls.json --split 0.8
```

**Output:**
```
Accuracy:    92.5%
Precision:   94.2%
Recall:      89.1%
F1-Score:    91.6%

⚠️  Missed Phishing URLs (showing first 10):
   • http://bankofamerica.myaccount.com/verify
   • https://amazon-account-verify.netlify.app
   ...

⚠️  False Alarms (showing first 10):
   • https://mail.google.com/mail/u/0/
   ...
```

### Step 3: Analyze Misclassifications

Find out WHY URLs are being misclassified:

```bash
python analyze_misclassifications.py --dataset your_phishing_urls.json
```

This shows:
- Which legitimate URLs are being wrongly flagged (false positives)
- Which phishing URLs are being missed (false negatives)
- Common features in misclassifications

---

## 🔧 Improving Performance

### Option A: Adjust Heuristic Thresholds

Edit `app/utils.py` to change the scoring rules:

```python
# Current scoring in heuristics_score():
if features["has_at_in_host"]:
    score += 0.40  # Change this weight based on your data

if features["is_shortener"]:
    score += 0.30  # Adjust shortener detection penalty

if features["is_typosquat"]:
    score += 0.35  # Adjust typosquatting penalty
```

**How to use misclassification data:**
- If legitimate URLs are being flagged (false positives), LOWER the penalty scores
- If phishing URLs are being missed (false negatives), RAISE the penalty scores

### Option B: Add New Features

If you notice patterns in your misclassified URLs, add new detection rules to `app/feature_extractor.py`:

```python
# Example: Detect suspicious keywords in domain
PHISHING_KEYWORDS = {"verify", "confirm", "update", "urgent", "action-required"}
has_phishing_keyword = any(kw in domain_before_at for kw in PHISHING_KEYWORDS)

return {
    "has_phishing_keyword": has_phishing_keyword,
    # ... other features
}
```

Then update the scoring in `utils.py`:

```python
if features.get("has_phishing_keyword"):
    score += 0.25
```

### Option C: Machine Learning Model (Advanced)

Train an actual ML classifier on the extracted features:

```python
# Create train_ml_model.py
from sklearn.ensemble import RandomForestClassifier
from app.feature_extractor import extract_features

X_train = []
y_train = []

for url, label in training_data:
    features = extract_features(url)
    # Convert feature dict to numeric vector
    feature_vector = [
        features["url_length"],
        features["num_dots"],
        features["count_special_chars"],
        float(features["has_at_in_host"]),
        float(features["is_shortener"]),
        float(features["is_typosquat"]),
        # ... more features
    ]
    X_train.append(feature_vector)
    y_train.append(1 if label == "phishing" else 0)

# Train model
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# Save model
import pickle
pickle.dump(model, open("phishing_model.pkl", "wb"))
```

Then use it in `app/llm_client.py` to blend with existing heuristics.

---

## 📊 Key Metrics Explained

| Metric | Formula | Meaning |
|--------|---------|---------|
| **Accuracy** | (TP + TN) / Total | % of correct predictions |
| **Precision** | TP / (TP + FP) | Of phishing flags, how many are correct? |
| **Recall** | TP / (TP + FN) | Of actual phishing, how many detected? |
| **F1-Score** | 2 × (P × R) / (P + R) | Balanced metric (precision + recall) |

- **TP**: Phishing correctly identified ✓
- **TN**: Legitimate correctly identified ✓
- **FP**: Legitimate wrongly flagged as phishing ✗ (false alarm)
- **FN**: Phishing missed ✗ (dangerous)

---

## 💡 Best Practices

1. **Start with heuristics** - They're fast, interpretable, and work well for obvious phishing patterns
2. **Evaluate regularly** - After each change, run evaluation to see if performance improved
3. **Balance false positives vs false negatives**
   - High FP: Users get annoyed with false alarms
   - High FN: Phishing gets through (security risk)
4. **Use both genuine and test data** - Prevents overfitting
5. **Update thresholds gradually** - Small changes, test, repeat

---

## 🔌 Integration with Flask API

To use your trained model in the web API:

1. Save your model:
   ```python
   import pickle
   pickle.dump(model, open("models/phishing_detector.pkl", "wb"))
   ```

2. Load in `app/llm_client.py`:
   ```python
   import pickle
   self.model = pickle.load(open("models/phishing_detector.pkl", "rb"))
   ```

3. Use in `analyze_url()`:
   ```python
   def analyze_url(self, url, features):
       # Use trained model
       prediction = self.model.predict([feature_vector])[0]
       confidence = self.model.predict_proba([feature_vector])[0][1]
       # Return result
   ```

---

## 🧪 Example: Full Training Workflow

```bash
# 1. Prepare dataset (my_phishing_urls.json)

# 2. Evaluate baseline
python train_and_evaluate.py --dataset my_phishing_urls.json --split 0.8

# Output shows 85% accuracy with lots of false positives

# 3. Analyze why
python analyze_misclassifications.py --dataset my_phishing_urls.json

# Output shows legitimate URLs with @ symbol are being flagged

# 4. Adjust scoring in app/utils.py
# Lower the "has_at_in_host" penalty from 0.40 to 0.25

# 5. Re-evaluate
python train_and_evaluate.py --dataset my_phishing_urls.json --split 0.8

# Output now shows 90% accuracy with better balance!

# 6. Test in web UI
python -m flask --app app.main run

# Visit http://localhost:5000 and test some URLs
```

---

## ❓ FAQ

**Q: How many phishing URLs do I need?**
A: Ideally 1000+, but the approach works with 100+. More data = better accuracy.

**Q: What if I don't have legitimate URLs?**
A: Your detector primarily needs PHISHING URLs for training. The feature extractor gives hints about legitimacy.

**Q: Can I use URLs from multiple sources?**
A: Yes! Combine phishing lists from:
- PhishTank (community list)
- OpenPhish
- AbuseCH
- Your own logs

**Q: How often should I retrain?**
A: At least monthly or when phishing tactics change (fake domains, new shorteners, etc.)

**Q: Will the LLM improve detection?**
A: Yes, but requires API key. The heuristics work offline and are good enough for most cases.
