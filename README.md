# SkillMatch — Smart Resume Analyzer & Job Matcher

A local full-stack student project using Flask, SQLite, PyMuPDF, HTML, CSS, and JavaScript.

## Features
- PDF resume text extraction (in memory; original PDF is not stored)
- Skill keyword overlap analysis against a pasted or sample job description
- Match score, matched skills, skills to review, and suggestions
- SQLite analysis history
- Responsive dashboard UI

## Run locally
1. Install Python 3.10+.
2. Open a terminal in this folder.
3. Create and activate a virtual environment (optional but recommended):
   - Windows: `python -m venv venv` then `venv\\Scripts\\activate`
   - macOS/Linux: `python3 -m venv venv` then `source venv/bin/activate`
4. Install packages: `pip install -r requirements.txt`
5. Start: `python app.py`
6. Open `http://127.0.0.1:5000` in your browser.

## Demo
- Upload a text-based PDF resume.
- Choose a sample role to fill its job description, or paste a custom description.
- Click Analyze resume.
- Open History to see saved reports.

## Important limitations
- The score is the percentage of detected job-description skills that were also detected in the resume. It is not an ATS score or hiring probability.
- Keyword matching can miss synonyms and context.
- Scanned/image-only PDFs are not supported because OCR is not included.
- This is a local prototype, not a production deployment. Before deployment, configure a strong `FLASK_SECRET_KEY`, disable debug mode, add authentication/CSRF protection, and review privacy requirements.
- The page loads Chart.js and fonts from CDNs, so those visual extras require internet; the core app works locally without them.
