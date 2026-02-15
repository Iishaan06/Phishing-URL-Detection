# 🎯 Complete Workflow: Training Your Phishing Detector with Your Dataset

## What You Now Have

I've created **4 new tools** to help you train and evaluate your phishing detector:

| Tool | What it Does |
|------|-------------|
| **train_and_evaluate.py** | Test detector accuracy, shows precision/recall/F1-score |
| **analyze_misclassifications.py** | Find which URLs are misclassified and why |
| **prepare_dataset.py** | Convert your data from TXT/CSV to JSON format |
| **TRAINING_GUIDE.md** | Deep dive into all training approaches |

Plus example datasets and documentation!

---

## 🚀 Complete Workflow (Step-by-Step)

### Phase 1: Prepare Your Data (15 min)

You have a list of phishing URLs. Convert them to a usable format:

#### Option A: Simple TXT file
Create `my_phishing_urls.txt`:
```
https://evil-bank.com phishing
https://real-bank.com legitimate
https://bit.ly/malware phishing
...
```

Then convert:
```powershell
python prepare_dataset.py --input my_phishing_urls.txt --output dataset.json
```

#### Option B: CSV file
Create `urls.csv`:
```csv
url,label
https://evil-site.com,phishing
https://legit-site.com,legitimate
...
```

Then convert:
```powershell
python prepare_dataset.py --input urls.csv --column-url url --column-label label --output dataset.json
```

#### Option C: Combine multiple sources
```powershell
python prepare_dataset.py --merge phishing1.txt legitimate_sites.csv phishbank.json --output combined_dataset.json
```

**Result:** `dataset.json` with your properly formatted data

---

### Phase 2: Test Baseline (5 min)

See how well your detector works RIGHT NOW:

```powershell
# Activate environment
.\env\Scripts\Activate.ps1

# Test on your data
python train_and_evaluate.py --dataset dataset.json --split 0.8
```

**You'll see:**
```
Accuracy:    85.3%
Precision:   91.2%
Recall:      78.9%
F1-Score:    84.6%

⚠️  Missed Phishing URLs:
    • https://micro-soft.com/login
    • https://safe-amazon-login.com
    ...
```

**This tells you:**
- ✅ What % of URLs are correctly classified
- ❌ Which phishing URLs are being missed (false negatives)
- ⚠️ Which legitimate URLs are wrongly flagged (false positives)

---

### Phase 3: Analyze Failures (5 min)

Find out WHY URLs are being misclassified:

```powershell
python analyze_misclassifications.py --dataset dataset.json
```

**Output:**
```
❌ FALSE POSITIVES: 12 legitimate URLs flagged as phishing
  • https://mail.google.com [@ in host + many subdomains]
  • https://accounts.microsoft.com [long domain]

❌ FALSE NEGATIVES: 8 phishing URLs not detected
  • https://evil.com [no obvious phishing markers]
  • https://safe-looking-domain.xyz [looks legitimate]

Common Features in Misclassifications:
  • has_at_in_host: 45.3%
  • shortener_domain: 32.1%
  • typosquatting_detected: 28.9%
```

---

### Phase 4: Improve the Detector (10-30 min)

Based on what you learned, make changes:

#### If too many legitimate sites are flagged (false positives):

Edit `app/utils.py`:

```python
def heuristics_score(features: Dict[str, Any]) -> Tuple[float, List[str]]:
    score = 0.0
    reasons = []

    # REDUCE these penalties:
    if features["has_at_in_host"]:
        score += 0.25  # was 0.40 - too aggressive
        reasons.append("URL contains '@' symbol")

    if features["shortener_domain"]:
        score += 0.15  # was 0.30
        reasons.append("Uses URL shortener")

    if features["typosquatting_detected"]:
        score += 0.20  # was 0.35
        reasons.append("Possible typosquatting")
```

#### If too many phishing URLs are missed (false negatives):

Either raise the penalties back up, OR lower the detection threshold:

```python
# In check_url() in app/main.py:
verdict = "phishing" if score >= 0.4 else "legitimate"  # was 0.5
```

#### If certain patterns aren't detected, add new features:

Add to `app/feature_extractor.py`:

```python
# Detect common phishing keywords
PHISHING_WORDS = {"verify", "confirm", "secure", "update", "urgent"}
suspicious_words = sum(1 for word in PHISHING_WORDS if word in host.lower())

return {
    "has_phishing_keywords": suspicious_words >= 2,
    ...
}
```

Then use it in `heuristics_score()`:

```python
if features.get("has_phishing_keywords"):
    score += 0.30
    reasons.append("URL contains suspicious keywords")
```

---

### Phase 5: Re-evaluate (5 min)

```powershell
python train_and_evaluate.py --dataset dataset.json --split 0.8
```

Check if your changes helped:
- ✅ Did accuracy improve?
- ✅ Did you reduce false positives?
- ✅ Did you catch more phishing?

If not improved, try different thresholds or features.

---

### Phase 6: Deploy (5 min)

Once you're happy with performance:

```powershell
# Start the Flask API
python -m flask --app app.main run
```

Visit `http://localhost:5000` and test your improved detector!

---

## 📊 Key Metrics at a Glance

### What Each Metric Means

| Metric | Formula | What It Tells You |
|--------|---------|------------------|
| **Accuracy** | (TP+TN)/(TP+TN+FP+FN) | Overall: % correct |
| **Precision** | TP/(TP+FP) | Quality: of phishing flags, how many are right? |
| **Recall** | TP/(TP+FN) | Coverage: of actual phishing, how many caught? |
| **F1-Score** | 2×(P×R)/(P+R) | Balance: harmonic mean of precision & recall |

### What Numbers Are Good?

**Target:**
- Accuracy: > 85%
- Precision: > 90% (avoid false alarms frustrating users)
- Recall: > 80% (catch most phishing)
- F1-Score: > 0.85

**Example - Good Balance:**
```
Accuracy: 88%
Precision: 92%
Recall: 82%
F1-Score: 0.87
```

---

## 🚨 Quick Troubleshooting

### Problem: Detection too aggressive (false positives high)

**Symptoms:** Legitimate sites flagged as phishing

**Solutions:**
1. Lower the score threshold: `verdict = "phishing" if score >= 0.6 else "legitimate"`
2. Reduce penalty weights in `heuristics_score()`
3. Add whitelist of domains (google.com, amazon.com, etc.)

### Problem: Detection too lenient (false negatives high)

**Symptoms:** Many phishing URLs not detected

**Solutions:**
1. Lower the threshold: `verdict = "phishing" if score >= 0.4 else "legitimate"`
2. Increase penalty weights in `heuristics_score()`
3. Add new feature detection for your phishing patterns

### Problem: Specific patterns not detected

**Symptoms:** Certain types of phishing always missed

**Solutions:**
1. Run `analyze_misclassifications.py` to find patterns
2. Add new feature detectors in `feature_extractor.py`
3. Update scoring in `heuristics_score()`
4. Re-evaluate and iterate

---

## 📋 Dataset Format Reference

### JSON (Recommended)
```json
[
  {"url": "https://evil.com", "label": "phishing"},
  {"url": "https://real.com", "label": "legitimate"}
]
```

### CSV
```
url,label
https://evil.com,phishing
https://real.com,legitimate
```

### TXT (Simple)
```
https://evil.com phishing
https://real.com legitimate
```

---

## 🔄 Iterative Improvement Cycle

```
1. Prepare Data
        ↓
2. Evaluate Baseline
   (e.g., 80% accuracy)
        ↓
3. Analyze Misclassifications
   (find patterns)
        ↓
4. Make Improvements
   (adjust thresholds/features)
        ↓
5. Re-Evaluate
   (e.g., 85% accuracy)
        ↓
6. Happy with results?
   ├─ NO: Go back to step 3
   └─ YES: Deploy!
```

**Each iteration typically takes 10-20 minutes.**

---

## 🎓 Advanced Options

### Custom ML Model

For more sophisticated detection, train an ML classifier:

```python
# In train_ml_model.py
from sklearn.ensemble import RandomForestClassifier

# Prepare training data
X_train = [feature_vector_1, feature_vector_2, ...]
y_train = [0, 1, ...]  # 0=legitimate, 1=phishing

model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# Use in app
prediction = model.predict(features)[0]
confidence = model.predict_proba(features)[0][1]
```

See `TRAINING_GUIDE.md` for full implementation.

---

## 📚 Full Documentation

- **QUICK_START.md** - Start here! (5-10 min read)
- **TRAINING_GUIDE.md** - Comprehensive guide (30 min read)
- **ARCHITECTURE.md** - How the detector works (technical)
- **README.md** - Project overview

---

## 🆘 Getting Help

**My script won't run:**
1. Check virtual environment is activated: `.\env\Scripts\Activate.ps1`
2. Check dependencies: `pip install -r requirements.txt`
3. Check Python version: `python --version` (need 3.9+)

**My dataset won't load:**
1. Check file path is correct
2. Check format (JSON/CSV/TXT) is supported
3. Run `python prepare_dataset.py --help` for format details

**Results don't look right:**
1. See "Quick Troubleshooting" section above
2. Run `analyze_misclassifications.py` to find patterns
3. Check `ARCHITECTURE.md` to understand feature extraction

---

## ✅ Checklist: Full Training Workflow

- [ ] Prepare phishing URL dataset
- [ ] Convert to JSON using `prepare_dataset.py`
- [ ] Run baseline evaluation: `train_and_evaluate.py`
- [ ] Analyze failures: `analyze_misclassifications.py`
- [ ] Identify improvement opportunities
- [ ] Update scoring in `app/utils.py` or features in `app/feature_extractor.py`
- [ ] Re-evaluate: `train_and_evaluate.py`
- [ ] Check if improved, repeat if not
- [ ] Deploy: `python -m flask --app app.main run`
- [ ] Test in browser at `http://localhost:5000`
- [ ] Monitor accuracy on future data
- [ ] Retrain monthly with new phishing patterns

---

## 📞 Next Steps

1. **Right now:** Test with sample data
   ```powershell
   python train_and_evaluate.py --dataset sample_dataset.json
   ```

2. **This hour:** Prepare your phishing URLs
   ```powershell
   python prepare_dataset.py --input my_urls.txt --output dataset.json
   ```

3. **This session:** Evaluate and improve
   ```powershell
   python train_and_evaluate.py --dataset dataset.json --split 0.8
   python analyze_misclassifications.py --dataset dataset.json
   # Then edit app/utils.py to improve...
   ```

4. **This week:** Deploy to production and monitor

Good luck! 🚀
