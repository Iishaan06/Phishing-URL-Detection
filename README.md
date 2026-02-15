# Phishing URL Detector

Detect suspicious links using deterministic URL features combined with an (optional) Large Language Model (LLM) for contextual reasoning.

## Project layout

```
phishing-url-detector/
├── app/
│   ├── __init__.py          # Flask application factory and config
│   ├── main.py              # API routes + CLI entry point
│   ├── feature_extractor.py # Feature engineering for URLs
│   ├── llm_client.py        # Wrapper for LLM or mock heuristic model
│   └── utils.py             # Validation helpers and prompt builders
├── frontend/
│   ├── index.html           # Minimal UI to submit URLs
│   ├── styles.css
│   └── script.js
├── tests/
│   ├── test_api.py          # Pytest coverage for health + inference routes
│   └── test_urls.json       # Sample labeled URLs
├── requirements.txt
├── run.sh                   # Convenience script to start Flask
└── README.md
```

## Quick start

Requires Python 3.9+.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m flask --app app.main run
```

Open `frontend/index.html` in your browser (or serve it via Live Server) and submit URLs to `http://localhost:5000/api/check`.


## Tests

```
pytest
```

`tests/test_urls.json` contains quick samples you can expand with your own curated datasets.

