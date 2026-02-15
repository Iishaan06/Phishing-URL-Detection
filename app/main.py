from flask import Blueprint, current_app, jsonify, request

from .feature_extractor import extract_features
from .llm_client import LLMClient, LLMClientError
from .trained_detector import TrainedMLDetector
from .utils import dedupe_reasons, is_valid_url


# Initialize the trained ML detector
ml_detector = TrainedMLDetector()


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

        # Use trained ML detector
        verdict, confidence, explanation, reasons = ml_detector.predict(url)
        
        if verdict == "error":
            # URL validation error
            return (
                jsonify({
                    "error": explanation,
                    "details": "Unable to analyze this URL"
                }),
                400,
            )
        
        # Get features for response
        features = extract_features(url)
        
        response = {
            "url": features["normalized_url"],
            "verdict": verdict,
            "confidence": round(confidence, 2),
            "explanation": explanation,
            "reasons": reasons if reasons else [],
            "features": features,
            "detection_method": "Machine Learning Model (trained on 549K phishing URLs)"
        }
        return jsonify(response)

    app.register_blueprint(api)


def main() -> None:
    from . import create_app

    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)


if __name__ == "__main__":
    main()

