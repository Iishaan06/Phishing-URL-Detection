from flask import Blueprint, current_app, jsonify, request

from .feature_extractor import extract_features
from .llm_client import LLMClient, LLMClientError
from .utils import dedupe_reasons, is_valid_url


def register_routes(app) -> None:
    api = Blueprint("api", __name__)

    @app.route("/")
    def index():
        """Serve the frontend HTML page."""
        from flask import send_from_directory
        import os
        frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
        return send_from_directory(frontend_dir, "index.html")

    @app.route("/<path:filename>")
    def static_files(filename):
        """Serve static files (CSS, JS) from frontend directory."""
        from flask import send_from_directory
        import os
        frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
        return send_from_directory(frontend_dir, filename)

    @api.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"})

    @api.route("/api/check", methods=["POST"])
    def check_url():
        payload = request.get_json(silent=True) or {}
        url = (payload.get("url") or "").strip()

        if not is_valid_url(url):
            return (
                jsonify({"error": "Please provide a valid HTTP or HTTPS URL."}),
                400,
            )

        features = extract_features(url)
        client = _build_client()

        try:
            llm_result = client.analyze_url(url, features)
        except LLMClientError as exc:
            # Log the error for debugging
            import logging
            logging.error(f"LLM Client Error: {exc}")
            return (
                jsonify({
                    "error": "LLM provider failure",
                    "details": str(exc),
                    "fallback": "Using heuristic analysis only"
                }),
                503,
            )
        except Exception as exc:
            # Catch any other unexpected errors
            import logging
            logging.error(f"Unexpected error in LLM analysis: {exc}")
            # Fall back to heuristics
            from .utils import heuristics_score
            score, reasons = heuristics_score(features)
            verdict = "phishing" if score >= 0.5 else "legitimate"
            confidence = min(score, 0.95) if verdict == "phishing" else (1.0 if score <= 0.1 else 1.0 - (score * 1.25))
            confidence = max(0.5, min(confidence, 1.0)) if verdict == "legitimate" else confidence
            
            response = {
                "url": features["normalized_url"],
                "verdict": verdict,
                "confidence": round(confidence, 2),
                "explanation": "LLM analysis unavailable. Using heuristic analysis only.",
                "reasons": reasons,
                "features": features,
            }
            return jsonify(response)

        response = {
            "url": features["normalized_url"],
            "verdict": llm_result.verdict,
            "confidence": llm_result.confidence,
            "explanation": llm_result.explanation,
            "reasons": dedupe_reasons(
                llm_result.reasons,
                features.get("matched_keywords", []),
            ),
            "features": features,
        }
        return jsonify(response)

    app.register_blueprint(api)


def _build_client() -> LLMClient:
    config = current_app.config
    return LLMClient(
        # Provider - LLM provider name
        provider=config.get("LLM_PROVIDER", "mock"),
        # API key - Set via environment variable LLM_API_KEY
        api_key=config.get("LLM_API_KEY"),
        base_url=config.get("LLM_BASE_URL"),
        # Version - Model version/name
        model=config.get("LLM_MODEL", "sonar-pro"),
        timeout=config.get("REQUEST_TIMEOUT", 8.0),
    )


def main() -> None:
    from . import create_app

    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)


if __name__ == "__main__":
    main()

