import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

from .utils import build_prompt, dedupe_reasons, heuristics_score


class LLMClientError(RuntimeError):
    """Raised when the configured LLM provider returns an error."""


@dataclass
class LLMResult:
    verdict: str
    confidence: float
    explanation: str
    reasons: List[str]


class LLMClient:
    """Light wrapper around either a live LLM API or a deterministic mock."""

    def __init__(
        self,
        provider: str = "mock",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 8.0,
        session: Optional[requests.Session] = None,
    ) -> None:
        # Provider - LLM provider name
        self.provider = provider
        # API key - Set via environment variable LLM_API_KEY
        self.api_key = api_key
        self.base_url = base_url
        # Version - Model version/name
        self.model = model
        self.timeout = timeout
        self.session = session or requests.Session()

    def analyze_url(self, url: str, features: Dict[str, Any]) -> LLMResult:
        """Return an LLMResult with verdict/confidence/explanation."""
        if self.provider == "mock" or not (self.api_key and self.base_url):
            return self._mock_response(features)
        return self._call_provider(url, features)

    def _call_provider(self, url: str, features: Dict[str, Any]) -> LLMResult:
        """Call the configured remote LLM provider.

        Currently this is tailored for Perplexity's /chat/completions endpoint,
        where the JSON body uses an OpenAI-style chat format and the model
        responds with text in choices[0].message.content.
        """
        prompt = build_prompt(url, features)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        if self.provider.lower() == "perplexity":
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.0,
            }
        else:
            # Generic fallback: treat provider like a simple completion endpoint
            payload = {
                "model": self.model,
                "input": prompt,
            }

        response = self.session.post(
            self.base_url,
            headers=headers,
            data=json.dumps(payload),
            timeout=self.timeout,
        )
        if response.status_code >= 400:
            raise LLMClientError(
                f"LLM provider error {response.status_code}: {response.text}"
            )

        data = response.json()

        if self.provider.lower() == "perplexity":
            try:
                message = data["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError) as exc:
                raise LLMClientError(f"Unexpected Perplexity response format: {data}") from exc
        else:
            message = data.get("output", "")

        # Try to extract JSON from the response (Perplexity might return text with JSON embedded)
        parsed = None
        try:
            # First, try to parse as pure JSON
            parsed = json.loads(message)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from the text (look for {...} pattern)
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', message, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
        
        if not parsed:
            # If we still can't parse JSON, fall back to heuristics only
            score, heuristics_reasons = heuristics_score(features)
            verdict = "phishing" if score >= 0.5 else "legitimate"
            confidence = min(score, 0.95) if verdict == "phishing" else (1.0 if score <= 0.1 else 1.0 - (score * 1.25))
            confidence = max(0.5, min(confidence, 1.0)) if verdict == "legitimate" else confidence
            
            # Try to extract verdict from LLM response text
            message_lower = message.lower()
            if "phishing" in message_lower and "legitimate" not in message_lower[:message_lower.find("phishing")]:
                verdict = "phishing"
                confidence = max(confidence, 0.7)
            elif "legitimate" in message_lower or "safe" in message_lower:
                verdict = "legitimate"
                confidence = max(confidence, 0.7)
            
            explanation = f"LLM analysis: {message[:200]}... (Using heuristics as fallback)"
            return LLMResult(verdict, round(confidence, 2), explanation, heuristics_reasons)

        verdict = parsed.get("verdict", "unknown")
        confidence = float(parsed.get("confidence", 0.5))
        explanation = parsed.get("explanation", "No explanation provided.")

        score, heuristics_reasons = heuristics_score(features)
        reasons = dedupe_reasons(
            parsed.get("reasons", []),
            heuristics_reasons,
        )
        blended_confidence = round(min(max(confidence, score), 1.0), 2)

        return LLMResult(verdict, blended_confidence, explanation, reasons)

    def _mock_response(self, features: Dict[str, Any]) -> LLMResult:
        score, reasons = heuristics_score(features)
        verdict = "phishing" if score >= 0.5 else "legitimate"
        
        # For legitimate URLs (score < 0.5), confidence should be high (close to 1.0)
        # For phishing URLs (score >= 0.5), confidence is the score itself
        if verdict == "phishing":
            confidence = min(score, 0.95)  # Cap at 95% for phishing
        else:
            # Legitimate: if score is very low (0.0-0.1), give high confidence (0.9-1.0)
            # If score is higher (0.1-0.5), reduce confidence proportionally
            if score <= 0.1:
                confidence = 1.0  # 100% confidence for clearly legitimate URLs
            else:
                # Scale from 0.9 to 0.5 as score goes from 0.1 to 0.5
                confidence = 1.0 - (score * 1.25)  # Ensures 0.1 -> 0.875, 0.5 -> 0.375
                confidence = max(0.5, min(confidence, 1.0))  # Clamp between 0.5 and 1.0
        
        if not reasons:
            reasons = ["No high-risk indicators detected; URL appears legitimate."]
        explanation = " ".join(reasons)
        return LLMResult(verdict, round(confidence, 2), explanation, reasons)

