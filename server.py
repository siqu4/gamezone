from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from pathlib import Path

# Папка, где находится server.py
BASE_DIR = Path(__file__).resolve().parent

# Файл базы данных
DB_PATH = BASE_DIR / "gamezone.db"

app = Flask(__name__, static_folder=None)


# =========================
# БАЗА ДАННЫХ
# =========================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            game TEXT NOT NULL,
            score INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# =========================
# ГЛАВНАЯ СТРАНИЦА
# =========================

@app.route("/")
def index():
    return send_from_directory(
        BASE_DIR,
        "index.html"
    )


# =========================
# ТАБЛИЦА ЛИДЕРОВ
# =========================

@app.route("/api/leaderboard", methods=["GET"])
def leaderboard():

    conn = get_db()

    rows = conn.execute("""
        SELECT
            name,
            game,
            MAX(score) AS score
        FROM scores
        GROUP BY name, game
        ORDER BY score DESC
        LIMIT 50
    """).fetchall()

    conn.close()

    result = []

    for row in rows:

        result.append({
            "name": row["name"],
            "game": row["game"],
            "score": row["score"]
        })

    return jsonify(result)


# =========================
# СОХРАНЕНИЕ РЕКОРДА
# =========================

@app.route("/api/score", methods=["POST"])
def add_score():

    data = request.get_json(
        silent=True
    ) or {}

    name = str(
        data.get(
            "name",
            "Игрок"
        )
    ).strip()[:20]

    game = str(
        data.get(
            "game",
            "Игра"
        )
    ).strip()[:30]


    try:

        score = int(
            data.get(
                "score",
                0
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify({
            "error":
            "score должен быть числом"
        }), 400


    if not name:

        name = "Игрок"


    if score < 0:

        return jsonify({
            "error":
            "Счёт не может быть отрицательным"
        }), 400


    # Защита от случайно огромного значения
    score = min(
        score,
        10_000_000
    )


    conn = get_db()


    # Ищем лучший результат
    # этого игрока в этой игре

    old = conn.execute(
        """
        SELECT MAX(score) AS best
        FROM scores
        WHERE name = ?
        AND game = ?
        """,
        (
            name,
            game
        )
    ).fetchone()


    best = old["best"]


    # Если результата ещё нет
    if best is None:

        conn.execute(
            """
            INSERT INTO scores
            (
                name,
                game,
                score
            )
            VALUES (?, ?, ?)
            """,
            (
                name,
                game,
                score
            )
        )


    # Если новый рекорд лучше старого
    elif score > best:

        conn.execute(
            """
            INSERT INTO scores
            (
                name,
                game,
                score
            )
            VALUES (?, ?, ?)
            """,
            (
                name,
                game,
                score
            )
        )


    # Старый результат лучше
    else:

        conn.close()

        return jsonify({
            "ok": True,
            "saved": False,
            "best": best
        })


    conn.commit()
    conn.close()


    return jsonify({
        "ok": True,
        "saved": True,
        "best": score
    })


# =========================
# ПРОВЕРКА СЕРВЕРА
# =========================

@app.route("/health")
def health():

    return jsonify({
        "status": "ok"
    })


# =========================
# ЗАПУСК
# =========================

if __name__ == "__main__":

    # Создаём базу данных
    init_db()

    # Для RelaxDev и других серверов
    # слушаем все подключения
    app.run(
        host="0.0.0.0",
        port=5000
    )
