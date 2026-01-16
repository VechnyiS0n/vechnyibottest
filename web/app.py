import os
import secrets
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
import db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev")


@app.route("/")
def index():
    lessons = db.fetch_all(
        "SELECT id, code, title, created_at FROM lessons ORDER BY created_at DESC"
    )

    total_feedback = db.fetch_one(
        "SELECT COUNT(*) AS cnt FROM feedback"
    )["cnt"]

    avg_rating = db.fetch_one(
        "SELECT COALESCE(AVG(rating), 0) AS avg FROM feedback"
    )["avg"]

    return render_template(
        "index.html",
        lessons=lessons,
        total_feedback=total_feedback,
        avg_rating=round(avg_rating, 2)
    )


@app.route("/lesson/<int:lesson_id>")
def lesson_page(lesson_id):
    lesson = db.fetch_one(
        "SELECT * FROM lessons WHERE id=%s",
        [lesson_id]
    )

    # Общая статистика по настроению
    stats = db.fetch_one(
        """
        SELECT
            COUNT(*) AS total,
            COALESCE(AVG(rating), 0)::float AS avg_rating,
            COALESCE(SUM(CASE WHEN mood='like' THEN 1 ELSE 0 END), 0) AS like_count,
            COALESCE(SUM(CASE WHEN mood='ok' THEN 1 ELSE 0 END), 0) AS ok_count,
            COALESCE(SUM(CASE WHEN mood='dislike' THEN 1 ELSE 0 END), 0) AS dislike_count
        FROM feedback
        WHERE lesson_id=%s
        """,
        [lesson_id]
    )

    # Распределение оценок (1–5)
    rating_stats = db.fetch_all(
        """
        SELECT rating, COUNT(*) AS count
        FROM feedback
        WHERE lesson_id=%s AND rating IS NOT NULL
        GROUP BY rating
        ORDER BY rating
        """,
        [lesson_id]
    )

    # Анонимные вопросы
    questions = db.fetch_all(
        "SELECT text FROM questions WHERE lesson_id=%s",
        [lesson_id]
    )

    return render_template(
        "lesson.html",
        lesson=lesson,
        stats=stats,
        rating_stats=rating_stats,
        questions=questions
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
