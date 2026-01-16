import os
import secrets
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
import db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev")


# Генерация короткого кода урока (например: X6BZLQ)
def gen_code(n=6):
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(n))


# Главная страница — панель учителя
@app.route("/")
def index():
    # Список уроков
    lessons = db.fetch_all(
    """
    SELECT
        l.id,
        l.code,
        l.title,
        l.created_at,

        COUNT(f.id) AS total,

        COALESCE(SUM(CASE WHEN f.mood = 'like' THEN 1 ELSE 0 END), 0) AS like_count,
        COALESCE(SUM(CASE WHEN f.mood = 'ok' THEN 1 ELSE 0 END), 0) AS ok_count,
        COALESCE(SUM(CASE WHEN f.mood = 'dislike' THEN 1 ELSE 0 END), 0) AS dislike_count

    FROM lessons l
    LEFT JOIN feedback f ON f.lesson_id = l.id
    GROUP BY l.id
    ORDER BY l.created_at DESC
    """
)



    # Общее количество оценок
    total_feedback = db.fetch_one(
        "SELECT COUNT(*) AS cnt FROM feedback"
    )["cnt"]

    # Средняя оценка по всем урокам
    avg_rating = db.fetch_one(
        "SELECT COALESCE(AVG(rating), 0) AS avg FROM feedback"
    )["avg"]

    return render_template(
        "index.html",
        lessons=lessons,
        total_feedback=total_feedback,
        avg_rating=round(avg_rating, 2)
    )


# Создание нового урока
@app.post("/lessons/create")
def create_lesson():
    title = request.form.get("title", "").strip()
    if not title:
        return redirect(url_for("index"))

    code = gen_code()
    db.execute(
        "INSERT INTO lessons (code, title) VALUES (%s, %s)",
        [code, title]
    )
    return redirect(url_for("index"))


# Страница конкретного урока
@app.route("/lesson/<int:lesson_id>")
def lesson_page(lesson_id):
    # Сам урок
    lesson = db.fetch_one(
        "SELECT * FROM lessons WHERE id=%s",
        [lesson_id]
    )

    # Общая статистика по настроению и оценкам
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

    # Распределение оценок (1–5) для столбчатого графика
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
        "SELECT text FROM questions WHERE lesson_id=%s ORDER BY id DESC",
        [lesson_id]
    )

    # 🔥 ОТЗЫВЫ И ОЦЕНКИ
    comments = db.fetch_all(
        """
        SELECT mood, rating, comment, created_at
        FROM feedback
        WHERE lesson_id=%s AND comment IS NOT NULL AND comment <> ''
        ORDER BY created_at DESC
        """,
        [lesson_id]
    )

    return render_template(
        "lesson.html",
        lesson=lesson,
        stats=stats,
        rating_stats=rating_stats,
        questions=questions,
        comments=comments
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
