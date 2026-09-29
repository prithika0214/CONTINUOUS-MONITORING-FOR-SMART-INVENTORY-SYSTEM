import os
import sys
import csv
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config import DATABASE, DATA_CSV

IST = ZoneInfo("Asia/Kolkata")
GROCERY_COLUMNS = (
    "product_id", "product_name", "category", "brand", "unit",
    "price_inr", "quantity", "minimum_stock", "supplier", "last_updated_ist"
)


def now_ist():
    return datetime.now(IST).isoformat(timespec="seconds")


def load_grocery_dataset(conn, csv_path=DATA_CSV, replace=False):
    with open(csv_path, newline="", encoding="utf-8-sig") as dataset_file:
        reader = csv.DictReader(dataset_file)
        if tuple(reader.fieldnames or ()) != GROCERY_COLUMNS:
            raise ValueError(f"Dataset columns must be exactly: {', '.join(GROCERY_COLUMNS)}")
        rows = list(reader)

    product_ids = [row["product_id"].strip() for row in rows]
    if not rows or any(not product_id for product_id in product_ids):
        raise ValueError("Dataset must contain products with non-empty product_id values")
    if len(product_ids) != len(set(product_ids)):
        raise ValueError("Dataset contains duplicate product_id values")

    cursor = conn.cursor()
    if replace:
        cursor.execute("DELETE FROM inventory")

    cursor.executemany(
        "INSERT OR IGNORE INTO suppliers (name) VALUES (?)",
        [(row["supplier"].strip(),) for row in rows],
    )
    suppliers = {
        row["name"]: row["id"]
        for row in cursor.execute("SELECT id, name FROM suppliers")
    }

    inserted = 0
    for row in rows:
        product_id = row["product_id"].strip()
        try:
            updated = datetime.fromisoformat(row["last_updated_ist"].strip())
            if updated.tzinfo is None:
                updated = updated.replace(tzinfo=IST)
            updated_ist = updated.astimezone(IST).isoformat(timespec="seconds")
            price = float(row["price_inr"])
            quantity = float(row["quantity"])
            minimum_stock = float(row["minimum_stock"])
            if price < 0 or quantity < 0 or minimum_stock < 0:
                raise ValueError("price and stock values must not be negative")
        except (TypeError, ValueError) as error:
            raise ValueError(f"Invalid dataset values for {product_id}: {error}") from error

        cursor.execute("""
            INSERT OR IGNORE INTO inventory (
                product_id, product_name, category, brand, unit, quantity,
                minimum_stock, price, supplier, supplier_id, last_updated_ist,
                barcode, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            product_id, row["product_name"].strip(), row["category"].strip(),
            row["brand"].strip(), row["unit"].strip(), quantity,
            minimum_stock, price, row["supplier"].strip(),
            suppliers[row["supplier"].strip()], updated_ist, product_id, updated_ist,
        ))
        inserted += cursor.rowcount

    return {"rows": len(rows), "inserted": inserted}

def get_db():
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'user')),
        email TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Suppliers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 3. Inventory Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id TEXT UNIQUE,
        product_name TEXT NOT NULL,
        category TEXT NOT NULL,
        brand TEXT NOT NULL DEFAULT '',
        unit TEXT NOT NULL DEFAULT 'piece',
        quantity INTEGER NOT NULL DEFAULT 0,
        minimum_stock INTEGER NOT NULL DEFAULT 5,
        price REAL NOT NULL DEFAULT 0.0,
        supplier TEXT NOT NULL DEFAULT '',
        last_updated_ist TEXT,
        barcode TEXT,
        supplier_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
    )
    """)

    inventory_columns = {
        row["name"] for row in cursor.execute("PRAGMA table_info(inventory)")
    }
    for column, declaration in (
        ("product_id", "TEXT"), ("brand", "TEXT NOT NULL DEFAULT ''"),
        ("unit", "TEXT NOT NULL DEFAULT 'piece'"),
        ("supplier", "TEXT NOT NULL DEFAULT ''"),
        ("last_updated_ist", "TEXT"),
    ):
        if column not in inventory_columns:
            cursor.execute(f"ALTER TABLE inventory ADD COLUMN {column} {declaration}")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_inventory_product_id ON inventory(product_id)")

    # 4. Transactions Table (Stock IN / Stock OUT)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        transaction_type TEXT NOT NULL CHECK(transaction_type IN ('IN', 'OUT')),
        quantity INTEGER NOT NULL,
        remarks TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES inventory (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    # 5. Stock Requests Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stock_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        reason TEXT,
        status TEXT NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending', 'Approved', 'Rejected')),
        admin_remarks TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (product_id) REFERENCES inventory (id)
    )
    """)

    # 6. Notifications Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    # 7. Audit Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 8. Sales History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        quantity_sold INTEGER NOT NULL,
        sale_date DATE NOT NULL,
        price_per_unit REAL NOT NULL,
        FOREIGN KEY (product_id) REFERENCES inventory (id)
    )
    """)

    # Keep existing accounts and create demo accounts only on a new database.
    admin_pw = generate_password_hash("admin123")
    user_pw = generate_password_hash("user123")

    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO users (username, password, name, role, email)
        VALUES (?, ?, ?, ?, ?)
        """, ("admin", admin_pw, "System Administrator", "admin", "admin@stockpulse.com"))

    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'user'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO users (username, password, name, role, email)
        VALUES (?, ?, ?, ?, ?)
        """, ("user", user_pw, "Inventory Clerk", "user", "clerk@stockpulse.com"))
    else:
        cursor.execute("UPDATE users SET password = ? WHERE username = 'user'", (user_pw,))

    # Seed Inventory from Indian Grocery Dataset
    cursor.execute("SELECT COUNT(*) FROM inventory")
    if cursor.fetchone()[0] == 0:
        load_grocery_dataset(conn)