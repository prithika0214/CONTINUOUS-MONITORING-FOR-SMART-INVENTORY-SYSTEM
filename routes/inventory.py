from flask import Blueprint, request
from database.database import get_db

inventory_bp = Blueprint("inventory", __name__)


@inventory_bp.route("", methods=["GET"])
def get_inventory():

    conn = get_db()

    products = conn.execute(
        "SELECT * FROM inventory"
    ).fetchall()

    conn.close()

    result = []

    for p in products:

        if p["quantity"] == 0:
            status = "Out of Stock"
        elif p["quantity"] <= p["minimum_stock"]:
            status = "Low Stock"
        else:
            status = "Healthy"

        result.append({
            "id": p["id"],
            "product_name": p["product_name"],
            "category": p["category"],
            "quantity": p["quantity"],
            "minimum_stock": p["minimum_stock"],
            "price": p["price"],
            "barcode": p["barcode"],
            "status": status
        })

    return result


@inventory_bp.route("", methods=["POST"])
def add_product():

    data = request.json

    conn = get_db()

    conn.execute("""
        INSERT INTO inventory
        (product_name, category, quantity,
         minimum_stock, price, barcode, supplier_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data["product_name"],
        data["category"],
        data["quantity"],
        data["minimum_stock"],
        data["price"],
        data.get("barcode"),
        data.get("supplier_id")
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Product added successfully"
    }