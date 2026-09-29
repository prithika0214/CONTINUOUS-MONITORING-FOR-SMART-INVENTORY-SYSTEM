from flask import Blueprint
from database.database import get_db

prediction_bp = Blueprint("prediction", __name__)


@prediction_bp.route("/<int:product_id>")
def prediction(product_id):

    conn = get_db()

    product = conn.execute("""
        SELECT product_name, quantity
        FROM inventory
        WHERE id=?
    """, (product_id,)).fetchone()

    conn.close()

    if not product:
        return {"message": "Product not found"}, 404

    # Simple baseline prediction
    predicted_demand = round(product["quantity"] * 0.25)

    return {
        "product": product["product_name"],
        "current_stock": product["quantity"],
        "predicted_demand": predicted_demand,
        "recommendation":
            "Consider restocking"
            if product["quantity"] < predicted_demand
            else "Stock level looks sufficient"
    }