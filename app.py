"""
SkillSync API — Resume-to-JD Matcher Microservice
===================================================
A lightweight Flask service that computes the compatibility between a
candidate's resume and a job description using TF-IDF vectorisation and
cosine similarity, then performs a simple gap analysis to surface keywords
present in the JD but missing from the resume.
"""

import re
import string
import threading
import time
import urllib.request

from flask import Flask, jsonify, request
from flask_cors import CORS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = Flask(__name__)
CORS(app) # This allows external web pages to communicate with your API

# ---------------------------------------------------------------------------
# Stop-word list (standard English stop words kept inline so the service has
# zero external data-file dependencies).
# ---------------------------------------------------------------------------
STOP_WORDS: set[str] = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you",
    "your", "yours", "yourself", "yourselves", "he", "him", "his", "himself",
    "she", "her", "hers", "herself", "it", "its", "itself", "they", "them",
    "their", "theirs", "themselves", "what", "which", "who", "whom", "this",
    "that", "these", "those", "am", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "having", "do", "does", "did", "doing",
    "a", "an", "the", "and", "but", "if", "or", "because", "as", "until",
    "while", "of", "at", "by", "for", "with", "about", "against", "between",
    "through", "during", "before", "after", "above", "below", "to", "from",
    "up", "down", "in", "out", "on", "off", "over", "under", "again",
    "further", "then", "once", "here", "there", "when", "where", "why",
    "how", "all", "both", "each", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too",
    "very", "s", "t", "can", "will", "just", "don", "should", "now",
    "must", "proficient", "seeking", "role", "requires", "require",
    "required", "handson", "building", "integrating", "utilizing",
    "team", "within", "experience", "candidate", "ideal", "working",
    "years", "knowledge", "ability", "strong", "understanding",
    "plus", "preferred", "environment", "using", "work", "skills",
    "development", "developer", "software", "engineer", "engineering"
    }

# ---------------------------------------------------------------------------
# Helper — text preprocessing
# ---------------------------------------------------------------------------

def preprocess(text: str) -> str:
    """Clean raw text for downstream NLP tasks.

    Steps
    -----
    1. Lower-case the entire string.
    2. Strip all punctuation characters.
    3. Remove standard English stop words.
    4. Collapse multiple whitespace into single spaces.

    Returns
    -------
    str
        The cleaned, whitespace-normalised string.
    """
    # 1. Normalise case
    text = text.lower()

    # 2. Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))

    # 3. Tokenise → drop stop words → rejoin
    tokens = [word for word in text.split() if word not in STOP_WORDS]

    # 4. Rejoin with single spaces
    return " ".join(tokens)


# ---------------------------------------------------------------------------
# Helper — compute match score
# ---------------------------------------------------------------------------

def compute_match_score(resume_clean: str, jd_clean: str) -> float:
    """Return a 0–100 percentage match score using TF-IDF + cosine similarity.

    Parameters
    ----------
    resume_clean : str
        Preprocessed resume text.
    jd_clean : str
        Preprocessed job-description text.

    Returns
    -------
    float
        Cosine similarity expressed as a percentage, rounded to two decimals.
    """
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([resume_clean, jd_clean])

    # cosine_similarity returns a 2×2 matrix; [0][1] is the score we want.
    score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

    return round(score * 100, 2)


# ---------------------------------------------------------------------------
# Helper — gap analysis (missing keywords)
# ---------------------------------------------------------------------------

def find_missing_keywords(resume_clean: str, jd_clean: str) -> list[str]:
    """Identify meaningful JD keywords that are absent from the resume.

    Uses a simple set-difference approach on the cleaned token sets.

    Returns
    -------
    list[str]
        Sorted list of words present in the JD but not in the resume.
    """
    resume_tokens = set(resume_clean.split())
    jd_tokens = set(jd_clean.split())

    missing = jd_tokens - resume_tokens
    return sorted(missing)


# ---------------------------------------------------------------------------
# API endpoint
# ---------------------------------------------------------------------------

@app.route("/match", methods=["POST"])
def match():
    """POST /match — Compare a resume against a job description.

    Expected JSON payload::

        {
            "resume_text": "...",
            "jd_text": "..."
        }

    Returns JSON::

        {
            "match_score": 72.35,
            "missing_keywords": ["kubernetes", "terraform", ...]
        }
    """
    # --- Input validation ------------------------------------------------
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    resume_text: str | None = data.get("resume_text")
    jd_text: str | None = data.get("jd_text")

    if not resume_text or not jd_text:
        return jsonify({
            "error": "Both 'resume_text' and 'jd_text' are required "
                     "and must be non-empty strings."
        }), 400

    # --- Preprocessing ----------------------------------------------------
    resume_clean = preprocess(resume_text)
    jd_clean = preprocess(jd_text)

    # Guard against edge case where preprocessing strips everything
    if not resume_clean or not jd_clean:
        return jsonify({
            "error": "After preprocessing, one or both texts were empty. "
                     "Please provide more substantive content."
        }), 422

    # --- ML scoring -------------------------------------------------------
    match_score = compute_match_score(resume_clean, jd_clean)

    # --- Gap analysis -----------------------------------------------------
    missing_keywords = find_missing_keywords(resume_clean, jd_clean)

    # --- Response ---------------------------------------------------------
    # Nuclear option: Force-scrub the final list before sending to React
    junk = {"must", "proficient", "seeking", "role", "requires", "required", "handson", "building", "integrating", "utilizing", "team", "within"}
    missing_keywords = [w for w in missing_keywords if w not in junk]

    return jsonify({
        "match_score": match_score,
        "missing_keywords": missing_keywords,
    })


# -----------------------------------------------------------------------------
# Bot Logic & Ping Route
# -----------------------------------------------------------------------------
@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "Awake"}), 200

def keep_awake():
    while True:
        time.sleep(840)  # Wait 14 minutes
        try:
            # We will replace this placeholder once Render gives us the real URL
            urllib.request.urlopen("https://YOUR_RENDER_URL_HERE.onrender.com/ping")
        except Exception:
            pass

# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    from waitress import serve
    
    # Start the background bot
    threading.Thread(target=keep_awake, daemon=True).start()
    
    print("Starting SkillSync API production server on http://0.0.0.0:5000")
    serve(app, host="0.0.0.0", port=5000)
