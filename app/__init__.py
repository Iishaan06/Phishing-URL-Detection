import os
from typing import Any, Dict, Optional

from flask import Flask
from flask_cors import CORS


def create_app(config: Optional[Dict[str, Any]] = None) -> Flask:
    """Application factory for the phishing URL detector."""
    app = Flask(__name__)

    default_config = {
        # Provider - LLM provider name (e.g., "perplexity", "openai", "mock")
        "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "mock"),
        # API key - Set via environment variable LLM_API_KEY
        "LLM_API_KEY": os.getenv("LLM_API_KEY"),
        "LLM_BASE_URL": os.getenv("LLM_BASE_URL"),
        # Version - Model version/name (e.g., "sonar-pro", "gpt-4")
        "LLM_MODEL": os.getenv("LLM_MODEL", "sonar-pro"),
        "REQUEST_TIMEOUT": float(os.getenv("REQUEST_TIMEOUT", "8.0")),
    }
    app.config.from_mapping(default_config)

    if config:
        app.config.update(config)

    CORS(app)

    from .main import register_routes

    register_routes(app)
    return app


# Gunicorn/Flask default entry point
app = create_app()

