# 📦 What's New: Training Tools for Your Phishing Detector

I've added **4 powerful new tools** to help you train and evaluate your phishing URL detector with your own dataset.

---

## 🎯 The Tools

### 1. **train_and_evaluate.py** - Test Your Detector

Evaluate accuracy on your dataset with detailed metrics.

```bash
# Quick test
python train_and_evaluate.py --dataset your_urls.json

# Split into 80% train, 20% test
python train_and_evaluate.py --dataset your_urls.json --split 0.8
```

**Output:**
- Accuracy, Precision, Recall, F1-Score
- Confusion matrix (TP, TN, FP, FN)
- List of misclassified URLs
- Statistics on phishing vs legitimate

---

### 2. **analyze_misclassifications.py** - Find Patterns in Errors

Understand WHY URLs are being misclassified.

```bash
python analyze_misclassifications.py --dataset your_urls.json
```

**Output:**
- False positives (legitimate URLs wrongly flagged)
- False negatives (phishing URLs missed)
- Common features in misclassifications
- Improvement suggestions

---

### 3. **prepare_dataset.py** - Convert Your Data

Convert phishing URLs from TXT/CSV/JSON to training format.

```bash
# From TXT file
python prepare_dataset.py --input phishing_urls.txt --output dataset.json

# From CSV with custom columns
python prepare_dataset.py --input data.csv --column-url "URL" --column-label "Type" --output dataset.json

# Merge multiple sources
python prepare_dataset.py --merge file1.txt file2.csv file3.json --output combined.json
```

**Supports:**
- TXT files (one URL per line, optional labels)
- CSV files (configurable column names)
- JSON files (standard format)
- Automatic deduplication

---

### 4. **sample_dataset.json** - Example Data

A small dataset (30 URLs) to test the tools immediately.

Try it now:
```bash
python train_and_evaluate.py --dataset sample_dataset.json
```

---

## 📚 Documentation

### **QUICK_START.md** ⭐ START HERE
- 5-minute guide to try the tools
- Step-by-step examples
- Common issues & fixes

### **COMPLETE_WORKFLOW.md**
- Full training workflow (all phases)
- Dataset preparation
- Evaluation and improvement cycle
- Troubleshooting guide

### **TRAINING_GUIDE.md**
- Deep dive into all training approaches
- Heuristic threshold tuning
- Machine learning model training
- LLM fine-tuning options
- Best practices

### **ARCHITECTURE.md** (already existed)
- How the detector works technically
- Feature extraction details
- Scoring mechanism

---

## 🚀 Quick Start (Right Now)

```powershell
# 1. Activate environment
cd d:\Phishing-URL-Detection
.\env\Scripts\Activate.ps1

# 2. Try with sample data
python train_and_evaluate.py --dataset sample_dataset.json

# 3. Analyze misclassifications
python analyze_misclassifications.py --dataset sample_dataset.json

# 4. View the documentation
# Open QUICK_START.md to learn how to use your own data
```

---

## 📊 How to Use with Your Data

### Step 1: Prepare
```bash
# Convert your phishing URLs to JSON
python prepare_dataset.py --input my_urls.txt --output dataset.json
```

### Step 2: Evaluate
```bash
# See baseline performance
python train_and_evaluate.py --dataset dataset.json --split 0.8
```

### Step 3: Analyze
```bash
# Find what's going wrong
python analyze_misclassifications.py --dataset dataset.json
```

### Step 4: Improve
- Edit `app/utils.py` to adjust scoring thresholds
- Edit `app/feature_extractor.py` to add new features
- See TRAINING_GUIDE.md for detailed instructions

### Step 5: Re-evaluate
```bash
# Check if your changes helped
python train_and_evaluate.py --dataset dataset.json --split 0.8
```

---

## 📋 Dataset Format

All tools work with this format:

```json
[
  {"url": "https://evil-domain.com/login", "label": "phishing"},
  {"url": "https://real-bank.com", "label": "legitimate"},
  {"url": "https://bit.ly/malware", "label": "phishing"},
  ...
]
```

Or convert from TXT/CSV using `prepare_dataset.py`.

---

## 📈 What You'll Learn

By using these tools, you'll understand:

- ✅ How well your detector performs
- ✅ Which phishing patterns it misses
- ✅ Which legitimate sites it wrongly flags
- ✅ How to improve detection accuracy
- ✅ How to balance precision vs recall
- ✅ How to train your own ML model

---

## 🎓 Example Workflow

```
1. Run: python train_and_evaluate.py --dataset sample_dataset.json
   → See: 66.7% accuracy, missed some phishing URLs

2. Run: python analyze_misclassifications.py --dataset sample_dataset.json
   → See: Common patterns in missed phishing (e.g., domains with @)

3. Edit: app/utils.py
   → Change: heuristics_score() to penalize @ domains more

4. Run: python train_and_evaluate.py --dataset sample_dataset.json
   → See: 75% accuracy - improved!

5. Run: python analyze_misclassifications.py --dataset sample_dataset.json
   → See: New patterns to fix

6. Repeat steps 3-5 until satisfied (ideally >85% accuracy)

7. Deploy: python -m flask --app app.main run
   → Test at http://localhost:5000
```

---

## 🔧 File Structure

```
d:\Phishing-URL-Detection\
├── train_and_evaluate.py ⭐ NEW - Evaluate accuracy
├── analyze_misclassifications.py ⭐ NEW - Find error patterns
├── prepare_dataset.py ⭐ NEW - Convert data formats
├── sample_dataset.json ⭐ NEW - Example data
├── QUICK_START.md ⭐ NEW - 5-min quick start
├── COMPLETE_WORKFLOW.md ⭐ NEW - Full training guide
├── TRAINING_GUIDE.md ⭐ NEW - Advanced techniques
├── ARCHITECTURE.md (existing)
├── README.md (existing)
├── requirements.txt (existing)
├── app/
│   ├── main.py (existing - Flask routes)
│   ├── feature_extractor.py (existing - URL feature extraction)
│   ├── llm_client.py (existing - LLM integration)
│   ├── utils.py (existing - scoring & prompts)
│   └── __init__.py (existing)
├── frontend/ (existing - web UI)
├── tests/ (existing - test suite)
└── env/ (existing - Python environment)
```

---

## 💡 Pro Tips

1. **Start with the sample data** to understand the tools
2. **Prepare your own dataset** using `prepare_dataset.py`
3. **Always split train/test** (use `--split 0.8`)
4. **Focus on recall first** (catch phishing), then precision (avoid false alarms)
5. **Iterate small** - change one parameter, test, then change next
6. **Save your best results** - keep track of threshold values that work
7. **Monitor over time** - phishing tactics evolve, retrain monthly

---

## ❓ FAQ

**Q: How many URLs do I need?**
A: At least 100 URLs (mix of phishing and legitimate). Ideally 1000+.

**Q: Can I use data from multiple sources?**
A: Yes! Use `prepare_dataset.py --merge` to combine multiple files.

**Q: What if I only have phishing URLs?**
A: The detector will still work (heuristics work without comparison). But accuracy improves with some legitimate URLs.

**Q: Can I use this to train an ML model?**
A: Yes! See TRAINING_GUIDE.md "Machine Learning Model" section.

**Q: Will the LLM improve detection?**
A: Yes, it adds contextual reasoning. Set environment variables to enable it (see README.md).

---

## 🚀 Next Steps

1. **Right now** (5 min):
   ```bash
   python train_and_evaluate.py --dataset sample_dataset.json
   ```

2. **Today** (30 min):
   - Prepare your phishing URLs
   - Convert to JSON with `prepare_dataset.py`
   - Evaluate with `train_and_evaluate.py`
   - Analyze with `analyze_misclassifications.py`

3. **This week** (iterative):
   - Make improvements based on analysis
   - Re-evaluate until you reach >85% accuracy
   - Deploy your improved detector

---

## 📞 Support

- **QUICK_START.md** - Start with this (clear examples)
- **TRAINING_GUIDE.md** - Deep technical guide
- **COMPLETE_WORKFLOW.md** - Step-by-step workflow
- **ARCHITECTURE.md** - Understand how it works

Good luck! 🎯
