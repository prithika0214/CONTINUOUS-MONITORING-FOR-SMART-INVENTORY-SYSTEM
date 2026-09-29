from flask import Blueprint
from database.database import get_db

user_bp = Blueprint("user", __name__)


@user_bp.route("/products")
def products():

    conn = get_db()

    products = conn.execute("""
        SELECT id, product_name, category,
               quantity, minimum_stock, price
        FROM inventory
        WHERE quantity > 0
    """).fetchall()

    conn.close()

    return [dict(p) for p in products]