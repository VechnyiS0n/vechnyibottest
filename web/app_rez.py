import os
import secrets
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
import db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev")

def gen_code(n=6):
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(n))

@app.get("/")
def index():
    lessons = db.fetch_all("SELECT id, code, title, created_at FROM lessons ORDER BY created_at DESC")
    return render_template("index.html", lessons=lessons)

@app.post("/lessons/create")
def create_lesson():
    title = request.form.get("title", "").strip()
    if not title:
        return redirect(url_for("index"))

    code = gen_code()
    db.execute("INSERT INTO lessons (code, title) VALUES (%s, %s)", [code, title])
    return redirect(url_for("index"))

@app.get("/lessons/<code>")
def lesson_page(code: str):
    lesson = db.fetch_one("SELECT id, code, title FROM lessons WHERE code=%s", [code.upper()])
    if not lesson:
        return "Lesson not found", 404

    stats = db.fetch_one("""
        SELECT
          AVG(rating)::float AS avg_rating,
          SUM(CASE WHEN mood='like' THEN 1 ELSE 0 END) AS like_count,
          SUM(CASE WHEN mood='ok' THEN 1 ELSE 0 END) AS ok_count,
          SUM(CASE WHEN mood='dislike' THEN 1 ELSE 0 END) AS dislike_count,
          COUNT(*) AS total
        FROM feedback
        WHERE lesson_id=%s
    """, [lesson["id"]])

    questions = db.fetch_all(
        "SELECT text, created_at FROM questions WHERE lesson_id=%s ORDER BY created_at DESC",
        [lesson["id"]]
    )

    comments = db.fetch_all(
        "SELECT comment, mood, rating, created_at FROM feedback WHERE lesson_id=%s AND comment IS NOT NULL ORDER BY created_at DESC",
        [lesson["id"]]
    )

    return render_template(
        "lesson.html",
        lesson=lesson,
        stats=stats,
        questions=questions,
        comments=comments
    )

if __name__ == "__main__":
    app.run(debug=True)
