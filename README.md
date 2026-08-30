# SkillSync API — Resume-to-JD Matcher Microservice

A lightweight Flask backend service that computes the compatibility between a candidate's resume and a job description. It uses TF-IDF vectorization and advanced Natural Language Processing (NLP) to extract technical skills and surface missing requirements.

## Key Features
* **Contextual NLP Extraction:** Utilizes `spaCy` Noun Chunking to capture complete technical phrases (e.g., "machine learning") rather than fragmented single words.
* **Negation Detection:** Leverages dependency parsing and proximity checks to identify and discard negated skills (e.g., accurately ignoring "AWS" when a user writes "I have no experience with AWS").
* **Automated Fluff Filtering:** Strips out corporate jargon and non-technical buzzwords using custom set-intersection filters.
* **Match Scoring:** Computes a 0-100% compatibility score using cosine similarity on a TF-IDF matrix.

## Tech Stack
* Python 3.11+
* Flask & Flask-CORS
* spaCy (`en_core_web_sm`)
* scikit-learn (TF-IDF)

## Local Setup
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt


## Download the core English NLP model:

   ```bash
    python -m spacy download en_core_web_sm 
   ```

## Run the local development server:

   ```bash
    python app.py
   ```

## Deployment Architecture
This API is optimized for deployment on Render as a web service.

```
Important Build Note: The PYTHON_VERSION environment variable must be explicitly set to a stable release (e.g., 3.11.9) in the Render dashboard. This prevents compiler crashes by allowing the backend to fetch pre-compiled binary wheels for C-based dependencies like spaCy, blis, and thinc.
```