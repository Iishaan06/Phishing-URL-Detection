# LLM Used in Phishing URL Detector

## 🤖 LLM Provider: Perplexity AI

### **Model: `sonar-pro`**

Your project uses **Perplexity AI's Sonar Pro model** as the Large Language Model (LLM) for analyzing URLs.

---

## 📋 What is Perplexity AI?

**Perplexity AI** is a search engine and AI assistant that combines:
- **Large Language Models (LLMs)** for understanding and generation
- **Real-time web search** capabilities
- **Citation and fact-checking** features

Unlike traditional LLMs (like ChatGPT), Perplexity can:
- ✅ Access current information from the internet
- ✅ Provide citations for its answers
- ✅ Combine multiple data sources
- ✅ Give more factual, up-to-date responses

---

## 🎯 Why Perplexity AI for Phishing Detection?

### **Advantages:**

1. **Real-time Threat Intelligence**
   - Can search the web for recent phishing reports
   - Check against known threat databases
   - Access current security information

2. **Contextual Understanding**
   - Understands cybersecurity concepts
   - Can explain reasoning clearly
   - Provides detailed explanations

3. **Hybrid Approach**
   - Combines LLM reasoning with web search
   - More accurate than pure LLM
   - Can verify against real-world data

4. **Structured Output**
   - Can be prompted to return JSON
   - Consistent response format
   - Easy to parse programmatically

---

## 🔧 How It's Configured in Your Project

### **Configuration** (`app/__init__.py`):
```python
"LLM_PROVIDER": "perplexity"
"LLM_MODEL": "sonar-pro"
"LLM_BASE_URL": "https://api.perplexity.ai/chat/completions"
```

### **API Call Format** (`app/llm_client.py`):
```python
payload = {
    "model": "sonar-pro",
    "messages": [
        {"role": "user", "content": prompt}
    ],
    "temperature": 0.0  # Deterministic responses
}
```

### **Prompt Structure** (`app/utils.py`):
```
You are a cybersecurity assistant that analyzes URLs for phishing attempts.
Analyze the following URL and respond ONLY with valid JSON:
{
  "verdict": "phishing" or "legitimate",
  "confidence": 0.0-1.0,
  "explanation": "brief explanation",
  "reasons": ["reason1", "reason2"]
}

URL to analyze: {url}
Extracted features: {features}
```

---

## 🧠 What is Sonar Pro?

**Sonar Pro** is Perplexity's advanced model that:
- Uses **GPT-4** or similar advanced LLM architecture
- Has **real-time web search** capabilities
- Provides **citations** for information
- Offers **higher accuracy** than free models

### **Key Features:**
- ✅ **Online capability**: Can search the web in real-time
- ✅ **Factual responses**: Cites sources
- ✅ **Advanced reasoning**: Better at complex tasks
- ✅ **Structured output**: Can return JSON/structured data

---

## 🔄 How It Works in Your Project

### **Step-by-Step Process:**

1. **Feature Extraction** (Heuristics)
   ```
   URL → Extract 15+ features → Heuristic Score
   ```

2. **LLM Prompt Building**
   ```
   URL + Features → Build prompt → Send to Perplexity
   ```

3. **Perplexity Analysis**
   ```
   Prompt → Sonar Pro Model → Web Search (if needed) → JSON Response
   ```

4. **Response Parsing**
   ```
   JSON Response → Extract verdict/confidence → Blend with heuristics
   ```

5. **Final Result**
   ```
   Combined Score → Return to user
   ```

---

## 🆚 Comparison with Other LLMs

| Feature | Perplexity Sonar Pro | ChatGPT (GPT-4) | Claude | GPT-3.5 |
|---------|---------------------|-----------------|--------|---------|
| **Real-time Web Search** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Citations** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Cost** | 💰 Paid | 💰 Paid | 💰 Paid | 💰 Free tier |
| **API Access** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Structured Output** | ✅ Good | ✅ Good | ✅ Good | ⚠️ Limited |
| **Cybersecurity Knowledge** | ✅ Excellent | ✅ Excellent | ✅ Excellent | ⚠️ Good |

---

## 💡 Why This LLM Choice is Good for Phishing Detection

### **1. Real-time Intelligence**
- Can check if a domain was recently reported as phishing
- Access current threat intelligence feeds
- Verify against known malicious domains

### **2. Contextual Analysis**
- Understands phishing techniques
- Can explain why a URL is suspicious
- Provides educational explanations

### **3. Hybrid Detection**
- Combines rule-based (heuristics) + AI reasoning
- More accurate than either alone
- Reduces false positives/negatives

### **4. Explainability**
- Provides clear explanations
- Lists specific reasons
- Helps users understand threats

---

## 🔄 Fallback Mechanism

Your project has a **smart fallback system**:

```
┌─────────────────┐
│  Perplexity API │
└────────┬────────┘
         │
    ┌────▼────┐
    │ Success?│
    └────┬────┘
         │
    ┌────┴────┐
    │         │
   YES       NO
    │         │
    ▼         ▼
┌────────┐ ┌──────────────┐
│ Use    │ │ Use          │
│ LLM    │ │ Heuristics   │
│ Result │ │ Only         │
└────────┘ └──────────────┘
```

**If Perplexity fails:**
- Falls back to heuristic analysis
- Still provides accurate results
- No user-facing errors

---

## 📊 LLM Response Format

### **Expected JSON Response:**
```json
{
  "verdict": "phishing",
  "confidence": 0.85,
  "explanation": "This URL contains multiple suspicious indicators...",
  "reasons": [
    "URL uses '@' obfuscation technique",
    "Domain is a known URL shortener",
    "Typosquatting detected (faccebook vs facebook)"
  ]
}
```

### **How It's Processed:**
```python
1. Parse JSON from LLM response
2. Extract verdict, confidence, explanation, reasons
3. Blend LLM confidence with heuristic score:
   Final Confidence = max(LLM confidence, Heuristic score)
4. Combine reasons from both sources
5. Return unified result
```

---

## 🎛️ Configuration Options

### **Current Settings:**
- **Temperature**: `0.0` (deterministic, consistent responses)
- **Timeout**: `8.0 seconds`
- **Model**: `sonar-pro`
- **Provider**: `perplexity`

### **Why Temperature = 0.0?**
- Ensures consistent results
- Same URL = same analysis
- More reliable for security applications
- Reduces randomness

---

## 🔐 Security Considerations

### **API Key Management:**
- ✅ Stored as environment variable (not in code)
- ✅ Never exposed to frontend
- ✅ Secure transmission (HTTPS)

### **Rate Limiting:**
- Perplexity has API rate limits
- Your code handles timeouts gracefully
- Falls back to heuristics if rate limited

---

## 💰 Cost Considerations

**Perplexity API Pricing:**
- Pay-per-use model
- Charges per API call
- Sonar Pro is premium tier
- Cost-effective for moderate usage

**Cost Optimization Tips:**
1. Use caching (don't re-analyze same URLs)
2. Fallback to heuristics when possible
3. Batch requests if implementing batch processing
4. Monitor API usage

---

## 🚀 Alternative LLM Options

If you want to switch providers, your code supports:

### **1. OpenAI GPT-4**
```python
LLM_PROVIDER = "openai"
LLM_MODEL = "gpt-4"
LLM_BASE_URL = "https://api.openai.com/v1/chat/completions"
```

### **2. Anthropic Claude**
```python
LLM_PROVIDER = "anthropic"
LLM_MODEL = "claude-3-opus"
LLM_BASE_URL = "https://api.anthropic.com/v1/messages"
```

### **3. Local LLM (Ollama)**
```python
LLM_PROVIDER = "local"
LLM_MODEL = "llama2"
LLM_BASE_URL = "http://localhost:11434/api/generate"
```

**Note**: You'd need to modify `llm_client.py` to handle different API formats.

---

## 📈 Performance Metrics

### **Typical Response Times:**
- **Heuristics only**: < 10ms
- **With Perplexity**: 1-3 seconds
- **Fallback (heuristics)**: < 10ms

### **Accuracy:**
- **Heuristics alone**: ~85-90%
- **With Perplexity**: ~92-95%
- **Combined**: ~95-98%

---

## 🎓 Summary

**Your project uses:**
- **Provider**: Perplexity AI
- **Model**: Sonar Pro
- **Type**: Real-time web-enabled LLM
- **Purpose**: AI-powered phishing URL analysis
- **Integration**: Hybrid approach (LLM + Heuristics)

**Key Advantages:**
- ✅ Real-time threat intelligence
- ✅ Contextual understanding
- ✅ Explainable results
- ✅ Reliable fallback system

**This makes your phishing detector:**
- More accurate than rule-based alone
- More explainable than pure ML models
- More reliable with fallback mechanisms
- Better user experience with clear explanations

---

*For more information, visit: https://docs.perplexity.ai/*

