const urlInput = document.getElementById("url-input");
const analyzeBtn = document.getElementById("analyze-btn");
const resultBox = document.getElementById("result");
const verdictEl = resultBox.querySelector(".verdict");
const confidenceEl = resultBox.querySelector(".confidence");
const explanationEl = resultBox.querySelector(".explanation");
const reasonsEl = resultBox.querySelector(".reasons");
const featuresEl = resultBox.querySelector(".features");

const API_BASE = window.API_BASE || "http://localhost:5000";

async function analyzeUrl() {
    const url = urlInput.value.trim();
    if (!url) {
        alert("Enter a URL to analyze.");
        return;
    }

    try {
        toggleLoading(true);
        const response = await fetch(`${API_BASE}/api/check`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url }),
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || "Request failed");
        }

        renderResult(data);
    } catch (error) {
        renderError(error.message);
    } finally {
        toggleLoading(false);
    }
}

function renderResult(data) {
    verdictEl.textContent = `Verdict: ${data.verdict.toUpperCase()}`;
    confidenceEl.textContent = `Confidence: ${(data.confidence * 100).toFixed(1)}%`;
    explanationEl.textContent = data.explanation;

    reasonsEl.innerHTML = "";
    data.reasons.forEach((reason) => {
        const pill = document.createElement("span");
        pill.textContent = reason;
        reasonsEl.appendChild(pill);
    });

    featuresEl.textContent = JSON.stringify(data.features, null, 2);
    resultBox.classList.remove("hidden");
}

function renderError(message) {
    verdictEl.textContent = "Verdict: ERROR";
    confidenceEl.textContent = "";
    explanationEl.textContent = message;
    reasonsEl.innerHTML = "";
    featuresEl.textContent = "";
    resultBox.classList.remove("hidden");
}

function toggleLoading(isLoading) {
    analyzeBtn.disabled = isLoading;
    analyzeBtn.textContent = isLoading ? "Analyzing..." : "Analyze";
}

analyzeBtn.addEventListener("click", analyzeUrl);
urlInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        analyzeUrl();
    }
});

