from flask import Blueprint, request
from database.database import get_db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.json

    username = data.get("username")
    password = data.get("password")

    conn = get_db()

    user = conn.execute("""
        SELECT * FROM users
        WHERE username = ? AND password = ?
    """, (username, password)).fetchone()

    conn.close()

    if user:

        return {
            "success": True,
            "user_id": user["id"],
            "name": user["name"],
            "role": user["role"]
        }

    return {
        "success": False,
        "message": "Invalid username or password"
    }, 401