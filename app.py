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
import spacy

# Load spaCy small English NLP model
nlp = spacy.load("en_core_web_sm")

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = Flask(__name__)
CORS(app) # This allows external web pages to communicate with your API

custom_junk = {"plus", "expertise", "foundation", "familiarity", "developer", "infrastructure", "role"}
negation_words = {"no", "not", "never", "without", "lack", "none", "zero"}

def extract_keywords(text):
    if not text:
        return set()

    doc = nlp(str(text).lower())
    keywords = set()

    for chunk in doc.noun_chunks:
        # 1. Grammatical Negation
        is_negated = any(child.dep_ == "neg" for child in chunk.root.head.children)

        # 2. Proximity Negation
        start_index = max(0, chunk.start - 3)
        preceding_tokens = [doc[i].text for i in range(start_index, chunk.start)]
        if any(neg in preceding_tokens for neg in negation_words):
            is_negated = True

        # Discard negated skills
        if is_negated:
            continue

        # Strip default stop words/punctuation from inside the chunk
        clean_words = [token.text for token in chunk if not token.is_stop and not token.is_punct]

        if clean_words:
            term = " ".join(clean_words)
            term_words = set(term.split())

            # 3. Fluff Filter (Only add if no junk words exist in the chunk)
            if not term_words.intersection(custom_junk) and len(term) > 1:
                keywords.add(term)

    return keywords

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

@app.route("/match", methods=["POST", "OPTIONS"])
def match():
    if request.method == "OPTIONS":
        return '', 200
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


    # POS Keyword extraction
    resume_keywords = extract_keywords(resume_text)
    jd_keywords = extract_keywords(jd_text)

    # Gap calculation
    missing_keywords = list(jd_keywords - resume_keywords)

    # Score calculation with divide-by-zero protection
    if len(jd_keywords) > 0:
        match_score = round((len(jd_keywords & resume_keywords) / len(jd_keywords)) * 100)
    else:
        match_score = 0

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
            urllib.request.urlopen("https://skillsync-y7yw.onrender.com")
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
