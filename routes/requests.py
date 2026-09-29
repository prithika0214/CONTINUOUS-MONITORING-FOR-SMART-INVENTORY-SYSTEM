from flask import Blueprint, request
from database.database import get_db

request_bp = Blueprint("requests", __name__)


@request_bp.route("", methods=["POST"])
def create_request():

    data = request.json

    conn = get_db()

    conn.execute("""
        INSERT INTO stock_requests
        (user_id, product_id, quantity, reason)
        VALUES (?, ?, ?, ?)
    """, (
        data["user_id"],
        data["product_id"],
        data["quantity"],
        data.get("reason", "")
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Stock request submitted"
    }


@request_bp.route("/user/<int:user_id>")
def user_requests(user_id):

    conn = get_db()

    rows = conn.execute("""
        SELECT stock_requests.*,
               inventory.product_name
        FROM stock_requests
        JOIN inventory
        ON stock_requests.product_id = inventory.id
        WHERE stock_requests.user_id = ?
        ORDER BY created_at DESC
    """, (user_id,)).fetchall()

    conn.close()

    return [dict(row) for row in rows]