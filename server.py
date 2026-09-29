import os
import json
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

# Папка проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Файл с данными
DATA_FILE = os.path.join(BASE_DIR, "data.json")


# =========================
# Работа с данными
# =========================

def load_data():
    if not os.path.exists(DATA_FILE):
        data = {
            "players": [],
            "scores": []
        }
        save_data(data)
        return data

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {
            "players": [],
            "scores": []
        }


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )


# =========================
# Главная страница GameZone
# =========================

@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


# =========================
# Проверка сервера
# =========================

@app.route("/api/status")
def status():
    return jsonify({
        "status": "online",
        "message": "GameZone backend работает!",
        "time": datetime.now().isoformat()
    })


# =========================
# Игроки
# =========================

@app.route("/api/players", methods=["GET"])
def get_players():
    data = load_data()

    return jsonify(data["players"])


@app.route("/api/players", methods=["POST"])
def create_player():
    data = load_data()

    body = request.get_json(silent=True) or {}

    username = str(body.get("username", "")).strip()

    if not username:
        return jsonify({
            "success": False,
            "error": "Введите имя игрока"
        }), 400

    if len(username) > 30:
        return jsonify({
            "success": False,
            "error": "Имя слишком длинное"
        }), 400

    # Проверяем существующего игрока
    for player in data["players"]:
        if player["username"].lower() == username.lower():
            return jsonify({
                "success": True,
                "player": player,
                "existing": True
            })

    player = {
        "id": len(data["players"]) + 1,
        "username": username,
        "created_at": datetime.now().isoformat()
    }

    data["players"].append(player)
    save_data(data)

    return jsonify({
        "success": True,
        "player": player,
        "existing": False
    }), 201


# =========================
# Результаты игр
# =========================

@app.route("/api/scores", methods=["POST"])
def add_score():
    data = load_data()

    body = request.get_json(silent=True) or {}

    username = str(body.get("username", "")).strip()
    game = str(body.get("game", "")).strip()

    if not username:
        return jsonify({
            "success": False,
            "error": "Не указано имя игрока"
        }), 400

    if not game:
        return jsonify({
            "success": False,
            "error": "Не указана игра"
        }), 400

    try:
        score = float(body.get("score", 0))
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "error": "Счёт должен быть числом"
        }), 400

    if score < 0:
        return jsonify({
            "success": False,
            "error": "Счёт не может быть отрицательным"
        }), 400

    result = {
        "id": len(data["scores"]) + 1,
        "username": username,
        "game": game,
        "score": score,
        "date": datetime.now().isoformat()
    }

    data["scores"].append(result)
    save_data(data)

    return jsonify({
        "success": True,
        "result": result
    }), 201


# =========================
# Все результаты
# =========================

@app.route("/api/scores", methods=["GET"])
def get_scores():
    data = load_data()

    scores = data["scores"]

    # Новые результаты сверху
    scores = sorted(
        scores,
        key=lambda x: x.get("date", ""),
        reverse=True
    )

    return jsonify(scores)


# =========================
# Таблица лидеров игры
# =========================

@app.route("/api/leaderboard/<game>")
def game_leaderboard(game):
    data = load_data()

    scores = [
        score
        for score in data["scores"]
        if score["game"].lower() == game.lower()
    ]

    # Больший результат выше
    scores.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return jsonify({
        "game": game,
        "leaderboard": scores[:20]
    })


# =========================
# Общая таблица лидеров
# =========================

@app.route("/api/leaderboard")
def leaderboard():
    data = load_data()

    scores = list(data["scores"])

    scores.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return jsonify({
        "leaderboard": scores[:50]
    })


# =========================
# 404
# =========================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Страница не найдена"
    }), 404


# =========================
# Запуск
# =========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    print("=================================")
    print("🎮 GameZone Backend")
    print("🚀 Сервер запущен")
    print(f"🌐 Порт: {port}")
    print("=================================")

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
