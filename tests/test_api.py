import json
from pathlib import Path

import pytest

from app import create_app


@pytest.fixture()
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client


def load_samples():
    path = Path(__file__).with_name("test_urls.json")
    return json.loads(path.read_text(encoding="utf-8"))


def test_health_endpoint(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_check_endpoint_returns_llm_fields(client):
    dataset = load_samples()
    for sample in dataset:
        resp = client.post("/api/check", json={"url": sample["url"]})
        assert resp.status_code == 200
        data = resp.get_json()
        assert "verdict" in data
        assert "confidence" in data
        assert "features" in data
        assert data["features"]["normalized_url"].startswith(("http://", "https://"))


def test_labels_align_with_heuristics(client):
    dataset = load_samples()
    for sample in dataset:
        resp = client.post("/api/check", json={"url": sample["url"]})
        verdict = resp.get_json()["verdict"]
        assert verdict == sample["label"]

