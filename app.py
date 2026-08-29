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
    # Add these to your existing set
    "job", "title", "company", "overview", "requirements", "join", "recent",
    "basic", "build", "like", "key", "motivated", "robust", "solutions",
    "user", "graduate", "student", "familiarity", "concepts", "foundational"
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
    "development", "developer", "software", "engineer", "engineering",
    # Extended standard English stop words and common verbs
        "into", "any", "could", "would", "might", "may", "cannot", "isn", "aren", "wasn",
        "weren", "hasn", "haven", "hadn", "doesn", "didn", "won", "wouldn", "shan", "shouldn",
        "mightn", "mustn", "let", "lets", "get", "gets", "got", "make", "makes", "made",
        "take", "takes", "took", "see", "sees", "saw", "say", "says", "said", "go", "goes",
        "went", "come", "comes", "came", "know", "knows", "knew", "think", "thinks", "thought",
        "look", "looks", "looked", "want", "wants", "wanted", "give", "gives", "gave", "use",
        "uses", "used", "find", "finds", "found", "tell", "tells", "told", "ask", "asks",
        "asked", "seem", "seems", "seemed", "feel", "feels", "felt", "try", "tries", "tried",
        "leave", "leaves", "left", "call", "calls", "called",

        # Generic Job Description and Resume filler words
        "responsibilities", "qualifications", "duties", "summary", "objective", "education",
        "location", "salary", "benefits", "apply", "resume", "cover", "letter", "equal",
        "opportunity", "employer", "flexible", "remote", "onsite", "hybrid", "fulltime",
        "parttime", "contract", "internship", "status", "description", "including", "related",
        "field", "degree", "bachelors", "masters", "phd", "demonstrated", "proven", "excellent",
        "good", "expert", "advanced", "intermediate", "beginner", "equivalent", "highly",
        "dynamic", "fast", "paced", "driven", "self", "starter", "track", "record", "successful",
        "successfully", "looking", "hire", "hiring", "member", "player", "communication",
        "written", "verbal", "interpersonal", "analytical", "problem", "solving", "detail",
        "oriented", "collaborative", "independent", "independently", "manage", "management",
        "lead", "leader", "leadership", "support", "assist", "ensure", "maintain", "create",
        "develop", "design", "implement", "execute", "deliver", "project", "projects",
        "business", "client", "clients", "customer", "customers", "users", "impact", "value",
        "best", "practices", "standard", "procedures", "policies", "regulatory", "compliance",
        "system", "systems", "application", "applications", "tool", "tools", "technology",
        "technologies", "platform", "platforms", "data", "information", "process", "processes",
        "strategy", "strategies", "plan", "plans", "goal", "goals", "objectives", "result",
        "results", "outcome", "outcomes", "metric", "metrics", "kpi", "kpis", "report",
        "reports", "analysis", "analytics", "test", "testing", "quality", "assurance", "qa",
        "production", "deployment", "deploy", "release", "maintenance", "troubleshoot",
        "resolve", "issue", "issues", "bug", "bugs", "feature", "features", "specifications",
        "document", "documentation", "review", "participate", "collaborate", "communicate",
        "present", "presentation", "meeting", "meetings", "daily", "weekly", "monthly",
        "annual", "year", "month", "months", "day", "days", "time", "schedule", "deadline",
        "deadlines", "prioritize", "tasks", "multiple", "various", "different", "new",
        "existing", "complex", "simple", "high", "low", "scale", "scalable", "performance",
        "perform", "performing", "optimize", "optimization", "improve", "improvement",
        "enhance", "enhancement", "innovate", "innovation", "creative", "creativity",
        "passion", "passionate", "focus", "focused", "orient", "mindset", "attitude",
        "culture", "fit", "diversity", "inclusion", "inclusive", "diverse", "background",
        "backgrounds", "opportunities", "grow", "growth", "learn", "learning", "train",
        "training", "mentor", "mentorship", "guide", "guidance", "coach", "coaching",
        "feedback", "evaluate", "evaluation", "assess", "assessment", "measure", "measurement",
        "monitor", "control", "direct", "supervise", "oversee", "coordinate", "facilitate",
        "organize", "achieve", "accomplish", "succeed", "success", "benefit", "advantage",
        "pro", "con", "risk", "mitigate", "mitigation", "challenge", "solution", "solve",
        "handle", "deal", "address", "tackle", "approach", "tactic", "method", "methodology",
        "procedure", "framework", "service", "product", "function", "functionality",
        "architecture", "code", "script", "program", "operate", "run", "debug", "fix",
        "repair", "upgrade", "update", "patch", "install", "configure", "setup", "initialize",
        "start", "stop", "restart", "pause", "cancel", "delete", "remove", "destroy", "clean",
        "clear", "format", "parse", "convert", "transform", "extract", "load", "save", "store",
        "read", "write"
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

    # Strip punctuation so words like Git/GitHub are split correctly
        import re
        resume_text = re.sub(r'[^\w\s]', ' ', resume_text)
        jd_text = re.sub(r'[^\w\s]', ' ', jd_text)
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
