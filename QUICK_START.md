# Quick Start: Training with Your Phishing URL Dataset

## 🎯 What You Have

You now have 3 new tools to train and evaluate your phishing detector:

| Tool | Purpose |
|------|---------|
| `train_and_evaluate.py` | Test detector accuracy on your dataset |
| `analyze_misclassifications.py` | Find why URLs are misclassified |
| `sample_dataset.json` | Example dataset to test with |
| `TRAINING_GUIDE.md` | Detailed training documentation |

---

## ⚡ Try It Now (5 minutes)

### Step 1: Activate your virtual environment

```powershell
cd d:\Phishing-URL-Detection
.\env\Scripts\Activate.ps1
```

### Step 2: Test with the sample dataset

```bash
# See how well the detector performs
python train_and_evaluate.py --dataset sample_dataset.json

# Split 80% train, 20% test
python train_and_evaluate.py --dataset sample_dataset.json --split 0.8
```

**Expected output:**
```
============================================================
  Test Set Evaluation Results
============================================================

Dataset Size:        6 URLs
  ├─ Phishing:       3
  └─ Legitimate:     3

Confusion Matrix:
  TP (Correct Phishing):    2
  TN (Correct Legitimate):  3
  FP (False Alarms):        0
  FN (Missed Phishing):     1

Metrics:
  Accuracy:    83.3%
  Precision:   100.0%
  Recall:      66.7%
  F1-Score:    80.0%

⚠️  Missed Phishing URLs (showing first 10):
    • https://micro soft.com/login.php (confidence: 0.62)
```

### Step 3: Analyze what went wrong

```bash
python analyze_misclassifications.py --dataset sample_dataset.json
```

This shows which URLs are being misclassified and why.

---

## 📥 Now Try with YOUR Data

### 1. **Prepare your phishing dataset**

Convert your phishing URLs to JSON format:

```json
[
  {"url": "https://your-phishing-site.com", "label": "phishing"},
  {"url": "https://real-bank.com", "label": "legitimate"},
  ...
]
```

### 2. **Evaluate on your data**

```bash
python train_and_evaluate.py --dataset your_phishing_urls.json --split 0.8
```

### 3. **Find improvement opportunities**

```bash
python analyze_misclassifications.py --dataset your_phishing_urls.json
```

Look for patterns in missed detections (false negatives).

### 4. **Improve the detector**

Edit `app/utils.py` to adjust scoring thresholds:

```python
# If many legitimate URLs are being flagged (false positives), lower these:
score += 0.40  # has_at_in_host weight
score += 0.30  # shortener weight  
score += 0.35  # typosquatting weight

# If many phishing URLs are being missed (false negatives), raise these
```

### 5. **Re-evaluate**

```bash
python train_and_evaluate.py --dataset your_phishing_urls.json --split 0.8
```

See if your changes improved accuracy!

---

## 📊 Understanding the Output

### Metrics

- **Accuracy**: Overall % of correct predictions
- **Precision**: Of detected phishing, how many are real phishing?
- **Recall**: Of all phishing URLs, how many did we catch?
- **F1-Score**: Balanced measure of precision + recall

### Confusion Matrix

```
TP (True Positive)   = Phishing correctly detected ✓
TN (True Negative)   = Legitimate correctly identified ✓
FP (False Positive)  = Legitimate wrongly flagged ✗
FN (False Negative)  = Phishing missed ✗
```

---

## 🔍 Common Issues & Fixes

### Issue: Too many false positives (legitimate URLs flagged as phishing)

**Solution:** Lower the scoring thresholds in `app/utils.py`

```python
# Reduce penalties
score += 0.20  # was 0.40 for @ in host
score += 0.15  # was 0.30 for shorteners
score += 0.20  # was 0.35 for typosquatting
```

### Issue: Too many false negatives (phishing URLs missed)

**Solution:** Raise the scoring thresholds

```python
# Increase penalties
score += 0.45
score += 0.40
score += 0.40

# Or lower the detection threshold from 0.5
verdict = "phishing" if score >= 0.4 else "legitimate"  # was 0.5
```

### Issue: Certain domain patterns not detected

**Solution:** Add new features in `app/feature_extractor.py`

```python
# Example: Flag URLs with suspicious keywords
PHISHING_KEYWORDS = {"verify", "confirm", "urgent", "action"}
has_phishing_word = any(kw in parsed.path.lower() for kw in PHISHING_KEYWORDS)

return {
    "has_phishing_keyword": has_phishing_word,
    # ... other features
}
```

---

## 🚀 Next Steps

1. ✅ Test with sample dataset
2. ✅ Prepare your phishing URL list
3. ✅ Convert to JSON format
4. ✅ Evaluate baseline performance
5. ✅ Analyze misclassifications
6. ✅ Fine-tune scoring thresholds
7. ✅ Re-evaluate and iterate
8. ✅ Deploy improved detector to Flask API

---

## 📚 Learn More

See **`TRAINING_GUIDE.md`** for:
- Detailed dataset format specifications
- Machine learning approach (sklearn)
- LLM fine-tuning options
- Performance optimization tips

---

## 💡 Pro Tips

- **Start simple**: Heuristics work great without ML complexity
- **Iterate small**: Adjust one parameter, test, then adjust next
- **Keep history**: Save your best thresholds before trying new ones
- **Test often**: Run evaluation after each code change
- **Balance metrics**: 90% recall with 50% precision is bad; aim for both >90%

---

## 🆘 Need Help?

**The detector not working as expected?**

1. Check `tests/test_urls.json` for expected input format
2. Run with `--split 0.8` to separate train/test data
3. Look at `analyze_misclassifications.py` output for patterns
4. Read `ARCHITECTURE.md` to understand how features are computed

**Want to train an ML model instead?**

See "Machine Learning Model (Advanced)" in `TRAINING_GUIDE.md`
