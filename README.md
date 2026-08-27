# SkillSync API — Resume-to-JD Matcher

A Flask microservice that scores how well a resume matches a job description. It uses TF-IDF vectorization and cosine similarity to compute a match score, then runs a gap analysis to pull out missing technical keywords while ignoring generic corporate filler words.

## Quick Start

**1. Create and activate a virtual environment**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Run the server**

```bash
python app.py
```

This project uses `waitress` as the WSGI server, so it's production-ready out of the box. Once running, it listens for requests at `http://localhost:5000`.

## Live Endpoints (Production)

Once deployed, point your frontend to the live URL instead of localhost.

Production API URL: `https://your-render-url-here.onrender.com`

## API Reference

### POST /match

| Field | Type | Required | Description |
|---|---|---|---|
| `resume_text` | string | Yes | The candidate's full resume content |
| `jd_text` | string | Yes | The target job description content |

**Example — cURL**

```bash
curl -X POST http://localhost:5000/match \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Experienced Python developer with expertise in Flask, REST APIs, PostgreSQL, Docker, and CI/CD pipelines. Built microservices handling 10k RPM.",
    "jd_text": "Looking for a Python developer skilled in Flask, Django, REST APIs, PostgreSQL, Kubernetes, Terraform, and CI/CD. Experience with microservices architecture required."
  }'
```

**Example — PowerShell**

```powershell
Invoke-RestMethod -Uri http://localhost:5000/match -Method Post `
  -ContentType "application/json" `
  -Body '{
    "resume_text": "Experienced Python developer with expertise in Flask, REST APIs, PostgreSQL, Docker, and CI/CD pipelines. Built microservices handling 10k RPM.",
    "jd_text": "Looking for a Python developer skilled in Flask, Django, REST APIs, PostgreSQL, Kubernetes, Terraform, and CI/CD. Experience with microservices architecture required."
  }'
```

**Sample response**

The filter strips out filler words like "looking," "skilled," and "experience," leaving only real technical gaps:

```json
{
  "match_score": 54.21,
  "missing_keywords": [
    "architecture",
    "django",
    "kubernetes",
    "terraform"
  ]
}
```

## Testing with Postman

1. Set the method to `POST` and the URL to `http://localhost:5000/match`.
2. Go to the Body tab, select `raw`, and choose `JSON`.
3. Paste the JSON payload from the cURL example above.
4. Click Send.

## Project Structure

```
SkillSync/
├── frontend/           # React / Vite frontend application
├── venv/               # Virtual environment (ignored in git)
├── app.py              # Flask application & ML logic
├── requirements.txt    # Python dependencies
└── README.md           # You are here
```