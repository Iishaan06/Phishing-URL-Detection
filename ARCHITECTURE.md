# Phishing URL Detector - Architecture & Mechanism

## 📐 Project Architecture

### **High-Level Overview**
```
┌─────────────┐
│   Browser   │ (Frontend)
│  (HTML/JS)  │
└──────┬──────┘
       │ HTTP POST /api/check
       ▼
┌─────────────────────────────────────┐
│      Flask Backend (Python)         │
│  ┌───────────────────────────────┐  │
│  │  1. URL Feature Extractor     │  │
│  │     - Parses URL structure    │  │
│  │     - Extracts 15+ features   │  │
│  └───────────┬───────────────────┘  │
│              │                      │
│  ┌───────────▼──────────────────┐   │
│  │  2. Heuristic Scorer         │   │
│  │     - Rule-based analysis    │   │
│  │     - Score: 0.0 - 0.95      │   │
│  └───────────┬──────────────────┘   │
│              │                      │
│  ┌───────────▼──────────────────┐   │
│  │  3. LLM Client               │   │
│  │     - Generic LLM provider    │   │
│  │     - Blends with heuristics |   │
│  └───────────┬──────────────────┘   │
│              │                      │
│  ┌───────────▼──────────────────┐   │
│  │  4. Response Formatter       │   │
│  │     - JSON response          │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
```

---

## 🔄 Request Flow Mechanism

### **Step-by-Step Process**

1. **User Input** (`frontend/script.js`)
   - User enters URL in browser
   - JavaScript sends POST request to `/api/check`

2. **URL Validation** (`app/main.py:36`)
   - Checks if URL has valid scheme (http/https)
   - Returns 400 error if invalid

3. **Feature Extraction** (`app/feature_extractor.py`)
   ```
   Input: "https://faccebook.com@is.gd/xA8ew2"
   
   Extracted Features:
   - normalized_url: "https://faccebook.com@is.gd/xA8ew2"
   - url_length: 38
   - has_at_in_host: True ⚠️
   - shortener_domain: True ⚠️
   - typosquatting_detected: True ⚠️
   - uses_https: True
   - count_special_chars: 2
   - ... (15 total features)
   ```

4. **Heuristic Scoring** (`app/utils.py:42`)
   ```
   Score Calculation:
   - has_at_in_host: +0.40
   - typosquatting: +0.35
   - shortener: +0.30
   - Both @ and shortener: +0.15
   ─────────────────────────────
   Total Score: 1.20 → Capped at 0.95
   Verdict: "phishing" (score ≥ 0.5)
   ```

5. **LLM Analysis** (`app/llm_client.py:47`)
   - Builds prompt with URL + features
   - Calls LLM provider API
   - Parses JSON response
   - Falls back to heuristics if LLM fails

6. **Confidence Blending** (`app/llm_client.py:140`)
   ```
   Final Confidence = max(LLM confidence, Heuristic score)
   Example: max(0.85, 0.95) = 0.95 (95%)
   ```

7. **Response** (`app/main.py:80`)
   ```json
   {
     "url": "https://faccebook.com@is.gd/xA8ew2",
     "verdict": "phishing",
     "confidence": 0.95,
     "explanation": "...",
     "reasons": ["URL contains '@'...", "Typosquatting..."],
     "features": {...}
   }
   ```

---

## 🧩 Component Breakdown

### **1. Feature Extractor** (`app/feature_extractor.py`)

**Purpose**: Extract measurable characteristics from URLs

**Key Features Detected**:
- **Structural**: URL length, dots, subdomains, path/query length
- **Security**: HTTPS usage, IP addresses
- **Suspicious Patterns**: 
  - `@` in host (obfuscation)
  - URL shorteners (is.gd, bit.ly)
  - Typosquatting (faccebook vs facebook)
  - Special characters, digits
  - Suspicious keywords (login, verify, password)

**Algorithm**:
```python
1. Normalize URL (add http:// if missing)
2. Parse URL components (scheme, netloc, path, query)
3. Extract host and domain parts
4. Check for @ obfuscation
5. Detect typosquatting (Levenshtein-like comparison)
6. Identify URL shorteners
7. Count suspicious patterns
```

---

### **2. Heuristic Scorer** (`app/utils.py:42`)

**Purpose**: Rule-based scoring system (0.0 = legitimate, 0.95 = highly suspicious)

**Scoring Logic**:
```
High-Confidence Indicators (can push score > 0.5 alone):
- @ in host: +0.40
- Typosquatting: +0.35
- URL shortener: +0.30
- Both @ + shortener: +0.15 bonus

Medium Indicators:
- IP address: +0.20
- Suspicious keywords: +0.20
- Deep subdomains (≥3): +0.15
- Long URL (>100 chars): +0.15

Low Indicators (only if already suspicious):
- No HTTPS: +0.10
- Many special chars (>5): +0.10
- Many digits (>10): +0.10
- Uncommon TLD: +0.10
```

**Verdict Threshold**: Score ≥ 0.5 = Phishing

---

### **3. LLM Client** (`app/llm_client.py`)

**Purpose**: AI-powered analysis using generic LLM API

**Two Modes**:
1. **Mock Mode** (no API key): Uses heuristics only
2. **Live Mode** (with API key): Calls LLM provider API

**Process**:
```python
1. Build prompt with URL + features
2. Send to LLM provider endpoint
3. Parse JSON response (with fallback parsing)
4. Extract: verdict, confidence, explanation, reasons
5. Blend LLM confidence with heuristic score
6. Return combined result
```

**Fallback Strategy**:
- If API fails → Use heuristics only
- If JSON parsing fails → Extract from text
- If all fails → Return heuristic verdict

---

### **4. Frontend** (`frontend/`)

**Components**:
- `index.html`: UI structure
- `script.js`: API communication
- `styles.css`: Styling

**User Flow**:
```
1. User enters URL
2. Click "Analyze" button
3. Show loading state
4. POST to /api/check
5. Display results:
   - Verdict (PHISHING/LEGITIMATE)
   - Confidence percentage
   - Explanation
   - List of reasons
   - Raw features (for debugging)
```

---

## 🎯 How It Works (Mechanism)

### **Dual-Layer Detection**

**Layer 1: Heuristics (Fast & Explainable)**
- Rule-based pattern matching
- Instant results (< 10ms)
- Always available (no API dependency)
- Transparent reasoning

**Layer 2: LLM Analysis (Context-Aware)**
- AI understands context
- Can catch subtle patterns
- Requires API call (~1-3 seconds)
- May be unavailable

**Hybrid Approach**:
- Heuristics provide baseline (always works)
- LLM enhances accuracy (when available)
- Confidence blending takes best of both

---

### **Confidence Calculation**

**For Phishing URLs** (score ≥ 0.5):
```
Confidence = Heuristic Score (capped at 95%)
```

**For Legitimate URLs** (score < 0.5):
```
If score ≤ 0.1: Confidence = 100%
If score 0.1-0.5: Confidence = 100% - (score × 1.25)
```

**With LLM**:
```
Final = max(LLM confidence, Heuristic score)
```

---

## 🚀 Improvement Suggestions

### **1. Accuracy Improvements**

#### **A. Machine Learning Model**
- **Current**: Rule-based + LLM
- **Improvement**: Train ML model on labeled dataset
- **Benefits**: 
  - Learn from historical phishing patterns
  - Better generalization
  - Adapt to new attack vectors
- **Implementation**: Use scikit-learn or TensorFlow

#### **B. Enhanced Feature Engineering**
- **Add DNS-based features**:
  - Domain age (new domains = suspicious)
  - WHOIS data (recent registration)
  - DNS record types (MX, TXT)
  - SSL certificate validity
- **Add Behavioral features**:
  - Domain popularity (Google Safe Browsing API)
  - Reputation scores (VirusTotal API)
  - Historical phishing reports

#### **C. Better Typosquatting Detection**
- **Current**: Simple character comparison
- **Improvement**: 
  - Use Levenshtein distance algorithm
  - Check homoglyph attacks (unicode lookalikes)
  - Compare against larger brand database

---

### **2. Performance Improvements**

#### **A. Caching**
```python
# Cache results for recently checked URLs
from functools import lru_cache
@lru_cache(maxsize=1000)
def check_url_cached(url_hash):
    # Store results for 1 hour
```

#### **B. Async Processing**
- Use async/await for LLM calls
- Process multiple URLs in parallel
- Queue system for batch processing

#### **C. Database Integration**
- Store URL analysis history
- Track false positives/negatives
- Build reputation database

---

### **3. User Experience Improvements**

#### **A. Real-time Analysis**
- Show results as user types
- Debounce input (wait 500ms after typing stops)
- Progressive loading indicators

#### **B. Visual Enhancements**
- Color-coded verdicts (red/green)
- Confidence meter visualization
- Risk level badges
- Historical trend charts

#### **C. Batch Analysis**
- Upload CSV file with URLs
- Analyze multiple URLs at once
- Export results to CSV/PDF

---

### **4. Security Improvements**

#### **A. Rate Limiting**
```python
from flask_limiter import Limiter
limiter = Limiter(app, key_func=get_remote_address)
@api.route("/api/check")
@limiter.limit("10 per minute")
```

#### **B. Input Sanitization**
- Validate URL format strictly
- Prevent SSRF attacks
- Sanitize user input before processing

#### **C. API Authentication**
- Add API keys for production
- User authentication system
- Request logging and monitoring

---

### **5. Scalability Improvements**

#### **A. Microservices Architecture**
```
┌─────────────┐
│   API GW    │
└──────┬──────┘
       │
   ┌───┴───┬──────────┬──────────┐
   │       │          │          │
┌──▼──┐ ┌──▼──┐   ┌──▼──┐   ┌──▼──┐
│ Feat│ │LLM  │   │Cache│   │DB   │
│ Ext │ │Svc  │   │Svc  │   │Svc  │
└─────┘ └─────┘   └─────┘   └─────┘
```

#### **B. Load Balancing**
- Multiple Flask instances
- Nginx reverse proxy
- Horizontal scaling

#### **C. Message Queue**
- Use Redis/RabbitMQ for async processing
- Decouple LLM calls from API responses
- Background job processing

---

### **6. Monitoring & Analytics**

#### **A. Logging**
```python
import logging
logging.basicConfig(level=logging.INFO)
logger.info(f"URL analyzed: {url}, Verdict: {verdict}")
```

#### **B. Metrics**
- Track accuracy (true positives/negatives)
- Monitor API response times
- Count requests per day/hour
- Error rate tracking

#### **C. Dashboard**
- Real-time statistics
- Accuracy trends
- Most common phishing patterns
- API usage metrics

---

### **7. Testing Improvements**

#### **A. Unit Tests**
- Test each component independently
- Mock LLM responses
- Test edge cases

#### **B. Integration Tests**
- Test full request flow
- Test error handling
- Test fallback mechanisms

#### **C. Performance Tests**
- Load testing (1000+ requests/sec)
- Stress testing
- Latency benchmarks

---

### **8. Documentation**

#### **A. API Documentation**
- Swagger/OpenAPI spec
- Interactive API docs
- Example requests/responses

#### **B. Code Documentation**
- Docstrings for all functions
- Architecture diagrams
- Deployment guides

---

## 📊 Current Limitations

1. **No Historical Data**: Doesn't learn from past analyses
2. **Limited Brand Database**: Only ~15 brands checked for typosquatting
3. **No Real-time Threat Intel**: Doesn't check against threat feeds
4. **Single LLM Provider**: Requires API key and base URL configuration
5. **No User Feedback Loop**: Can't improve from user corrections
6. **No Batch Processing**: One URL at a time
7. **No Caching**: Re-analyzes same URLs repeatedly

---

## 🎓 Learning Resources

- **URL Structure**: RFC 3986 (URI specification)
- **Phishing Techniques**: OWASP Top 10, APWG reports
- **Machine Learning**: scikit-learn documentation
- **Flask Best Practices**: Flask documentation
- **API Design**: RESTful API design principles

---

## 🔧 Quick Wins (Easy Improvements)

1. ✅ Add more brand names to typosquatting list
2. ✅ Implement URL caching (1 hour TTL)
3. ✅ Add rate limiting (prevent abuse)
4. ✅ Improve error messages (more user-friendly)
5. ✅ Add request logging
6. ✅ Create API documentation
7. ✅ Add unit tests for feature extractor
8. ✅ Implement health check endpoint (already exists!)

---

## 📈 Future Roadmap

**Phase 1** (Current): Basic detection with heuristics + LLM
**Phase 2**: Add ML model, caching, rate limiting
**Phase 3**: Multi-provider LLM, threat intel integration
**Phase 4**: User accounts, batch processing, analytics dashboard
**Phase 5**: Mobile app, browser extension, API marketplace

---

*Last Updated: 2024*

