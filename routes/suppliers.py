from flask import Blueprint, request
from database.database import get_db

supplier_bp = Blueprint("suppliers", __name__)


@supplier_bp.route("", methods=["GET"])
def get_suppliers():

    conn = get_db()

    suppliers = conn.execute(
        "SELECT * FROM suppliers"
    ).fetchall()

    conn.close()

    return [dict(s) for s in suppliers]


@supplier_bp.route("", methods=["POST"])
def add_supplier():

    data = request.json

    conn = get_db()

    conn.execute("""
        INSERT INTO suppliers
        (name, phone, email, address)
        VALUES (?, ?, ?, ?)
    """, (
        data["name"],
        data["phone"],
        data["email"],
        data["address"]
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Supplier added"
    }