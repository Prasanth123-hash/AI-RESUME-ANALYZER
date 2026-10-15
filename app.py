import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import fitz  # PyMuPDF
from flask import Flask, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "resume_analyzer.db"
UPLOAD_FOLDER = BASE_DIR / "uploads"
ALLOWED_EXTENSIONS = {"pdf"}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "local-demo-change-me")
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
UPLOAD_FOLDER.mkdir(exist_ok=True)

SKILL_ALIASES = {
    "python": ["python"],
    "java": ["java"],
    "javascript": ["javascript", "js"],
    "typescript": ["typescript"],
    "c++": ["c++"],
    "c#": ["c#"],
    "sql": ["sql", "structured query language"],
    "html": ["html"],
    "css": ["css"],
    "react": ["react", "react.js"],
    "node.js": ["node.js", "nodejs"],
    "flask": ["flask"],
    "django": ["django"],
    "fastapi": ["fastapi"],
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning"],
    "natural language processing": ["natural language processing", "nlp"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "tensorflow": ["tensorflow"],
    "pytorch": ["pytorch"],
    "data analysis": ["data analysis", "data analytics"],
    "excel": ["excel", "microsoft excel"],
    "power bi": ["power bi"],
    "tableau": ["tableau"],
    "git": ["git", "github"],
    "docker": ["docker"],
    "aws": ["aws", "amazon web services"],
    "azure": ["azure", "microsoft azure"],
    "communication": ["communication", "communicate"],
    "teamwork": ["teamwork", "team work"],
    "problem solving": ["problem solving", "problem-solving"],
    "rest api": ["rest api", "restful api", "rest apis"],
    "mongodb": ["mongodb", "mongo db"],
    "sqlite": ["sqlite"],
    "postgresql": ["postgresql", "postgres"],
}

SAMPLE_JOBS = {
    "Python Developer": """We are looking for a Python Developer with Python, Flask, SQL, REST API, Git, and problem-solving skills. Experience with SQLite, testing, and teamwork is helpful.""",
    "Data Analyst": """We are looking for a Data Analyst with Python, SQL, Excel, data analysis, pandas, NumPy, Power BI, communication, and problem-solving skills.""",
    "Machine Learning Intern": """We are looking for a Machine Learning Intern with Python, machine learning, pandas, NumPy, scikit-learn, data analysis, Git, and communication skills.""",
    "Frontend Developer": """We are looking for a Frontend Developer with HTML, CSS, JavaScript, React, Git, REST API, communication, and teamwork skills.""",
}

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                filename TEXT NOT NULL,
                job_title TEXT NOT NULL,
                match_score REAL NOT NULL,
                matched_skills TEXT NOT NULL,
                missing_skills TEXT NOT NULL,
                suggestions TEXT NOT NULL
            )
        """)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_pdf_text(file_storage):
    # Parse in memory; the uploaded resume is not saved to disk.
    raw = file_storage.read()
    if not raw.startswith(b"%PDF"):
        raise ValueError("This file does not look like a valid PDF.")
    doc = fitz.open(stream=raw, filetype="pdf")
    try:
        text = "\n".join(page.get_text("text") for page in doc)
    finally:
        doc.close()
    if not text.strip():
        raise ValueError("No selectable text was found. This demo does not run OCR on scanned PDFs.")
    return text[:200_000]

def contains_term(text, term):
    # Match words/phrases without false positives inside unrelated words.
    pattern = r"(?<![a-z0-9+#.])" + re.escape(term.lower()) + r"(?![a-z0-9+#.])"
    return re.search(pattern, text.lower()) is not None

def find_skills(text):
    found = []
    for canonical, aliases in SKILL_ALIASES.items():
        if any(contains_term(text, alias) for alias in aliases):
            found.append(canonical)
    return found

def build_analysis(resume_text, job_text):
    resume_skills = find_skills(resume_text)
    job_skills = find_skills(job_text)
    if not job_skills:
        raise ValueError("We couldn't detect known skills in that job description. Try a sample job or include specific skills.")
    matched = [skill for skill in job_skills if skill in resume_skills]
    missing = [skill for skill in job_skills if skill not in resume_skills]
    score = round((len(matched) / len(job_skills)) * 100, 1)
    suggestions = []
    if missing:
        suggestions.append("Review these job-related skills and build evidence for the ones you genuinely know: " + ", ".join(missing[:10]) + ".")
    if not contains_term(resume_text, "project") and not contains_term(resume_text, "projects"):
        suggestions.append("Consider adding a Projects section with your role, tools used, and measurable outcomes.")
    if not contains_term(resume_text, "education"):
        suggestions.append("Check that your Education section is clearly labeled.")
    if not suggestions:
        suggestions.append("Good keyword coverage. Tailor your project and experience bullets to the specific responsibilities in this job description.")
    return resume_skills, job_skills, matched, missing, score, suggestions

@app.route("/")
def index():
    return render_template("index.html", sample_jobs=SAMPLE_JOBS)

@app.route("/analyze", methods=["POST"])
def analyze():
    resume = request.files.get("resume")
    job_title = request.form.get("job_title", "Custom Job").strip()[:100] or "Custom Job"
    job_description = request.form.get("job_description", "").strip()[:20_000]
    sample_key = request.form.get("sample_job", "").strip()
    if not resume or not resume.filename:
        flash("Choose a PDF resume to analyze.", "error")
        return redirect(url_for("index"))
    if not allowed_file(resume.filename):
        flash("Only PDF files are accepted.", "error")
        return redirect(url_for("index"))
    if sample_key in SAMPLE_JOBS and not job_description:
        job_description = SAMPLE_JOBS[sample_key]
        job_title = sample_key
    if not job_description:
        flash("Paste a job description or choose a sample job role.", "error")
        return redirect(url_for("index"))
    try:
        resume_text = extract_pdf_text(resume)
        _, job_skills, matched, missing, score, suggestions = build_analysis(resume_text, job_description)
    except (ValueError, fitz.FileDataError) as exc:
        flash(str(exc), "error")
        return redirect(url_for("index"))
    filename = secure_filename(resume.filename)[:180] or "resume.pdf"
    matched_str = ", ".join(matched)
    missing_str = ", ".join(missing)
    suggestions_str = "\n".join(suggestions)
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO analyses
            (created_at, filename, job_title, match_score, matched_skills, missing_skills, suggestions)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (datetime.now().strftime("%Y-%m-%d %H:%M"), filename, job_title, score,
              matched_str, missing_str, suggestions_str))
        analysis_id = cursor.lastrowid
    return render_template(
        "result.html", analysis_id=analysis_id, filename=filename, job_title=job_title,
        score=score, job_skills=job_skills, matched=matched, missing=missing,
        suggestions=suggestions, resume_skill_count=len(find_skills(resume_text))
    )

@app.route("/history")
def history():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM analyses ORDER BY id DESC LIMIT 100").fetchall()
    return render_template("history.html", analyses=rows)

@app.route("/history/<int:analysis_id>")
def history_detail(analysis_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
    if row is None:
        flash("Analysis not found.", "error")
        return redirect(url_for("history"))
    return render_template("history_detail.html", item=row)

@app.route("/health")
def health():
    return {"status": "ok"}

@app.errorhandler(413)
def too_large(_error):
    flash("File is too large. Maximum upload size is 5 MB.", "error")
    return redirect(url_for("index"))

init_db()

if __name__ == "__main__":
    app.run(debug=True)
