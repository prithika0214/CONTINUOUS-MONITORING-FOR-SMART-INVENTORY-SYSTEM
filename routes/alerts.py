from flask import Blueprint
from database.database import get_db

alert_bp = Blueprint("alerts", __name__)


@alert_bp.route("")
def alerts():

    conn = get_db()

    products = conn.execute("""
        SELECT * FROM inventory
        WHERE quantity <= minimum_stock
    """).fetchall()

    conn.close()

    result = []

    for p in products:

        status = (
            "Out of Stock"
            if p["quantity"] == 0
            else "Low Stock"
        )

        result.append({
            "product": p["product_name"],
            "quantity": p["quantity"],
            "status": status
        })

    return result