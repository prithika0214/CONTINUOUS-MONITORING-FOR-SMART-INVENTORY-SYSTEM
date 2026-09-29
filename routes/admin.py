from flask import Blueprint
from database.database import get_db

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/dashboard")
def dashboard():

    conn = get_db()

    total = conn.execute(
        "SELECT COUNT(*) AS count FROM inventory"
    ).fetchone()["count"]

    low = conn.execute("""
        SELECT COUNT(*) AS count
        FROM inventory
        WHERE quantity > 0
        AND quantity <= minimum_stock
    """).fetchone()["count"]

    out = conn.execute("""
        SELECT COUNT(*) AS count
        FROM inventory
        WHERE quantity = 0
    """).fetchone()["count"]

    value = conn.execute("""
        SELECT SUM(quantity * price) AS value
        FROM inventory
    """).fetchone()["value"]

    conn.close()

    return {
        "total_products": total,
        "low_stock": low,
        "out_of_stock": out,
        "inventory_value": value or 0
    }