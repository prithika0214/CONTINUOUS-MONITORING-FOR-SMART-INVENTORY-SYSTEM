from flask import Blueprint, request
from database.database import get_db

transaction_bp = Blueprint("transactions", __name__)


@transaction_bp.route("", methods=["GET"])
def get_transactions():

    conn = get_db()

    rows = conn.execute("""
        SELECT * FROM transactions
        ORDER BY created_at DESC
    """).fetchall()

    conn.close()

    return [dict(row) for row in rows]


@transaction_bp.route("", methods=["POST"])
def create_transaction():

    data = request.json

    product_id = data["product_id"]
    quantity = data["quantity"]
    transaction_type = data["transaction_type"]

    conn = get_db()

    product = conn.execute(
        "SELECT quantity FROM inventory WHERE id=?",
        (product_id,)
    ).fetchone()

    if not product:
        conn.close()
        return {"message": "Product not found"}, 404

    current = product["quantity"]

    if transaction_type == "OUT":

        if current < quantity:
            conn.close()
            return {"message": "Insufficient stock"}, 400

        new_quantity = current - quantity

    else:

        new_quantity = current + quantity

    conn.execute("""
        UPDATE inventory
        SET quantity=?
        WHERE id=?
    """, (new_quantity, product_id))

    conn.execute("""
        INSERT INTO transactions
        (product_id, user_id, transaction_type, quantity)
        VALUES (?, ?, ?, ?)
    """, (
        product_id,
        data.get("user_id"),
        transaction_type,
        quantity
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "new_quantity": new_quantity
    }