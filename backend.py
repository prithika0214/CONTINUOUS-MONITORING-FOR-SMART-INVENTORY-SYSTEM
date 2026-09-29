"""
Continuous Monitoring Smart Inventory System - Backend Engine
All backend logic encapsulated in this single file.
Features:
- Thread-safe SQLite database with rich multi-rack retail & warehouse sample dataset
- Background Continuous Monitoring Engine (daemon thread)
- Dynamic store clock, real-time telemetry, and continuous stock depletion/consumption
- Real-time alerts: Out of Stock, Low Stock Reorders, Expired Items, and Nearly Expiring Rack Clearance
- Automated and manual Purchase Order placement and fulfillment system
- Full REST API endpoints
"""

import os
import sys
import time
import json
import sqlite3
import threading
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
IST = ZoneInfo('Asia/Kolkata')
from flask import Flask, request, jsonify
from flask_cors import CORS

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.db")
db_lock = threading.Lock()

app = Flask(__name__)
CORS(app)

# ==============================================================================
# DATABASE INITIALIZATION & SAMPLE DATASET
# ==============================================================================

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(force_reset=False):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()

        if force_reset:
            cursor.execute("DROP TABLE IF EXISTS inventory")
            cursor.execute("DROP TABLE IF EXISTS purchase_orders")
            cursor.execute("DROP TABLE IF EXISTS activity_logs")
            cursor.execute("DROP TABLE IF EXISTS system_state")

        # Table: Inventory
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                rack_id TEXT NOT NULL,
                shelf_level TEXT NOT NULL,
                batch_no TEXT NOT NULL,
                current_stock INTEGER NOT NULL,
                min_stock INTEGER NOT NULL,
                reorder_threshold INTEGER NOT NULL,
                max_capacity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                cost_price REAL NOT NULL,
                discount_percent REAL DEFAULT 0.0,
                expiry_date TEXT NOT NULL,
                supplier_name TEXT NOT NULL,
                status TEXT NOT NULL,
                last_updated TEXT NOT NULL
            )
        """)

        # Table: Purchase Orders
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchase_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                po_number TEXT UNIQUE NOT NULL,
                sku TEXT NOT NULL,
                item_name TEXT NOT NULL,
                rack_id TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_cost REAL NOT NULL,
                total_cost REAL NOT NULL,
                supplier TEXT NOT NULL,
                status TEXT NOT NULL,
                order_time TEXT NOT NULL,
                expected_arrival TEXT NOT NULL,
                eta_seconds INTEGER NOT NULL,
                remaining_seconds INTEGER NOT NULL
            )
        """)

        # Table: Activity Logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                sku TEXT,
                rack_id TEXT
            )
        """)

        # Table: System State (Simulated clock, simulation speed, running state)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                simulated_time TEXT NOT NULL,
                is_running INTEGER DEFAULT 1,
                sim_speed_multiplier REAL DEFAULT 1.0,
                total_sales_count INTEGER DEFAULT 0,
                total_orders_placed INTEGER DEFAULT 0
            )
        """)

        cursor.execute("SELECT COUNT(*) FROM system_state WHERE id = 1")
        if cursor.fetchone()[0] == 0:
            now_iso = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO system_state (id, simulated_time, is_running, sim_speed_multiplier, total_sales_count, total_orders_placed)
                VALUES (1, ?, 1, 1.0, 0, 0)
            """, (now_iso,))

        # Seed Sample Dataset if empty
        cursor.execute("SELECT COUNT(*) FROM inventory")
        if cursor.fetchone()[0] == 0:
            seed_sample_dataset(cursor)

        conn.commit()
        conn.close()

def seed_sample_dataset(cursor):
    base_date = datetime.now(IST)
    now_str = base_date.strftime("%Y-%m-%d %H:%M:%S")

    import csv
    import os
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "stockpulse_indian_grocery_dataset.csv")
    sample_items = []
    
    # We map the Indian grocery dataset to our schema
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            # assign fake racks based on category or index
            rack = f"Rack {(i%6)+1}-01"
            shelf = f"Shelf {(i%3)+1}"
            
            product_id = row.get("product_id", f"SKU-{i}")
            name = row.get("product_name", "Unknown")
            cat = row.get("category", "General")
            qty = int(float(row.get("quantity", 0)))
            min_stock = int(float(row.get("minimum_stock", 5)))
            price = float(row.get("price_inr", 0))
            supplier = row.get("supplier", "Unknown")
            
            sample_items.append((
                product_id, name, cat, rack, shelf, f"BAT-{product_id}",
                qty, min_stock, min_stock + 5, max(100, qty + 20),
                price, price * 0.5, 0.0,
                (base_date + timedelta(days=90)).strftime("%Y-%m-%d"),
                supplier, "HEALTHY", now_str
            ))

    cursor.executemany("""
        INSERT INTO inventory (
            sku, name, category, rack_id, shelf_level, batch_no,
            current_stock, min_stock, reorder_threshold, max_capacity,
            unit_price, cost_price, discount_percent, expiry_date,
            supplier_name, status, last_updated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_items)

    cursor.execute("""
        INSERT INTO activity_logs (timestamp, event_type, severity, message, sku, rack_id)
        VALUES (?, 'SYSTEM', 'INFO', 'Continuous Monitoring Smart Inventory System initialized with Indian Grocery dataset.', NULL, 'ALL')
    """, (now_str,))

# ==============================================================================
# CONTINUOUS MONITORING & TELEMETRY ENGINE
# ==============================================================================

class ContinuousMonitoringEngine(threading.Thread):
    """
    Background daemon thread that runs continuously.
    - Advances simulated store clock.
    - Simulates real-time retail consumption (stock depletion).
    - Checks expiry status (Expired vs Nearly Expiring).
    - Checks stock thresholds (No Stock vs Low Stock).
    - Processes active purchase orders and auto-restocks items upon arrival.
    - Emits timestamped activity logs for audits.
    """
    def __init__(self, interval_seconds=3.0):
        super().__init__(daemon=True)
        self.interval_seconds = interval_seconds
        self.running = True
        self._step_counter = 0

    def run(self):
        while self.running:
            try:
                self.cycle_update()
            except Exception as e:
                print(f"[Engine Error]: {e}", file=sys.stderr)
            time.sleep(self.interval_seconds)

    def cycle_update(self):
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Read system state
            cursor.execute("SELECT simulated_time, is_running, sim_speed_multiplier, total_sales_count, total_orders_placed FROM system_state WHERE id = 1")
            state_row = cursor.fetchone()
            if not state_row:
                conn.close()
                return

            sim_time_str = state_row["simulated_time"]
            is_running = bool(state_row["is_running"])
            multiplier = float(state_row["sim_speed_multiplier"])
            sales_count = state_row["total_sales_count"]

            if not is_running:
                conn.close()
                return

            # 1. Advance simulated time (e.g. 1 real cycle = 2 hours * multiplier)
            current_dt = datetime.strptime(sim_time_str, "%Y-%m-%d %H:%M:%S")
            advanced_dt = current_dt + timedelta(minutes=int(30 * multiplier))
            now_iso = advanced_dt.strftime("%Y-%m-%d %H:%M:%S")
            current_date_str = advanced_dt.strftime("%Y-%m-%d")

            # 2. Process Purchase Orders: Decrement remaining seconds & deliver if ready
            cursor.execute("SELECT * FROM purchase_orders WHERE status IN ('PENDING', 'IN_TRANSIT')")
            pos = cursor.fetchall()
            for po in pos:
                time_step = int(self.interval_seconds * multiplier)
                new_remaining = max(0, po["remaining_seconds"] - time_step)
                if new_remaining <= 0:
                    # PO Delivered! Auto-restock inventory
                    cursor.execute("""
                        UPDATE purchase_orders 
                        SET status = 'DELIVERED', remaining_seconds = 0
                        WHERE id = ?
                    """, (po["id"],))

                    # Increase stock in inventory
                    cursor.execute("""
                        UPDATE inventory
                        SET current_stock = MIN(max_capacity, current_stock + ?),
                            last_updated = ?
                        WHERE sku = ?
                    """, (po["quantity"], now_iso, po["sku"]))

                    cursor.execute("""
                        INSERT INTO activity_logs (timestamp, event_type, severity, message, sku, rack_id)
                        VALUES (?, 'RESTOCK', 'SUCCESS', ?, ?, ?)
                    """, (now_iso, f"PO #{po['po_number']} DELIVERED! Restocked {po['quantity']} units of '{po['item_name']}' on {po['rack_id']}.", po["sku"], po["rack_id"]))
                elif new_remaining <= po["eta_seconds"] // 2:
                    cursor.execute("UPDATE purchase_orders SET status = 'IN_TRANSIT', remaining_seconds = ? WHERE id = ?", (new_remaining, po["id"]))
                else:
                    cursor.execute("UPDATE purchase_orders SET remaining_seconds = ? WHERE id = ?", (new_remaining, po["id"]))

            # 3. Simulate continuous stock consumption (customer purchases) every 2-3 cycles
            self._step_counter += 1
            if self._step_counter % 2 == 0:
                cursor.execute("SELECT id, sku, name, current_stock, rack_id, discount_percent FROM inventory WHERE current_stock > 0 AND status != 'EXPIRED'")
                available_items = cursor.fetchall()
                if available_items:
                    # Pick 1-2 random items to sell
                    selected_sample = random.sample(available_items, min(len(available_items), random.randint(1, 2)))
                    for item in selected_sample:
                        # Discounted items sell faster
                        sell_qty = random.randint(1, 3) if item["discount_percent"] > 0 else random.randint(1, 2)
                        sell_qty = min(sell_qty, item["current_stock"])
                        if sell_qty > 0:
                            new_stk = item["current_stock"] - sell_qty
                            cursor.execute("UPDATE inventory SET current_stock = ?, last_updated = ? WHERE id = ?", (new_stk, now_iso, item["id"]))
                            sales_count += sell_qty
                            cursor.execute("""
                                INSERT INTO activity_logs (timestamp, event_type, severity, message, sku, rack_id)
                                VALUES (?, 'SALE', 'INFO', ?, ?, ?)
                            """, (now_iso, f"Sale recorded: {sell_qty} units of '{item['name']}' from {item['rack_id']}. (Remaining: {new_stk})", item["sku"], item["rack_id"]))

            # 4. Continuous Evaluation of Stock and Expiry States
            cursor.execute("SELECT id, sku, name, rack_id, current_stock, min_stock, reorder_threshold, expiry_date, status, discount_percent FROM inventory")
            all_items = cursor.fetchall()

            for itm in all_items:
                expiry_dt = datetime.strptime(itm["expiry_date"], "%Y-%m-%d")
                days_left = (expiry_dt.date() - advanced_dt.date()).days
                stk = itm["current_stock"]
                old_status = itm["status"]

                if days_left < 0:
                    new_status = "EXPIRED"
                elif stk == 0:
                    new_status = "OUT_OF_STOCK"
                elif stk <= itm["reorder_threshold"]:
                    new_status = "LOW_STOCK"
                elif days_left <= 5:
                    new_status = "NEAR_EXPIRY"
                else:
                    new_status = "HEALTHY"

                if new_status != old_status:
                    cursor.execute("UPDATE inventory SET status = ?, last_updated = ? WHERE id = ?", (new_status, now_iso, itm["id"]))
                    # Log state transitions
                    if new_status == "EXPIRED":
                        cursor.execute("""
                            INSERT INTO activity_logs (timestamp, event_type, severity, message, sku, rack_id)
                            VALUES (?, 'ALERT_EXPIRED', 'CRITICAL', ?, ?, ?)
                        """, (now_iso, f"CRITICAL: '{itm['name']}' on {itm['rack_id']} has EXPIRED! Quarantine immediately from rack!", itm["sku"], itm["rack_id"]))
                    elif new_status == "OUT_OF_STOCK":
                        cursor.execute("""
                            INSERT INTO activity_logs (timestamp, event_type, severity, message, sku, rack_id)
                            VALUES (?, 'ALERT_NO_STOCK', 'CRITICAL', ?, ?, ?)
                        """, (now_iso, f"ALERT: '{itm['name']}' is OUT OF STOCK on {itm['rack_id']}. Place replenishment order immediately!", itm["sku"], itm["rack_id"]))
                    elif new_status == "LOW_STOCK":
                        cursor.execute("""
                            INSERT INTO activity_logs (timestamp, event_type, severity, message, sku, rack_id)
                            VALUES (?, 'ALERT_LOW_STOCK', 'WARNING', ?, ?, ?)
                        """, (now_iso, f"REMINDER: '{itm['name']}' stock ({stk}) is below reorder threshold ({itm['reorder_threshold']}). Minimum order needed: {itm['min_stock']} units.", itm["sku"], itm["rack_id"]))
                    elif new_status == "NEAR_EXPIRY":
                        cursor.execute("""
                            INSERT INTO activity_logs (timestamp, event_type, severity, message, sku, rack_id)
                            VALUES (?, 'ALERT_NEAR_EXPIRY', 'WARNING', ?, ?, ?)
                        """, (now_iso, f"URGENT: '{itm['name']}' in {itm['rack_id']} expires in {days_left} days! Sell these products as soon as possible in that rack!", itm["sku"], itm["rack_id"]))

            # Save updated system state
            cursor.execute("""
                UPDATE system_state 
                SET simulated_time = ?, total_sales_count = ?
                WHERE id = 1
            """, (now_iso, sales_count))

            conn.commit()
            conn.close()

# ==============================================================================
# REST API ENDPOINTS
# ==============================================================================

@app.route("/api/status", methods=["GET"])
def get_system_status():
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM system_state WHERE id = 1")
        state = dict(cursor.fetchone())

        # Compute summary metrics
        cursor.execute("SELECT COUNT(*) FROM inventory")
        total_skus = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(current_stock) FROM inventory")
        total_units = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(current_stock * unit_price) FROM inventory")
        inventory_value = round(cursor.fetchone()[0] or 0.0, 2)

        cursor.execute("SELECT COUNT(*) FROM inventory WHERE current_stock == 0")
        out_of_stock_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM inventory WHERE current_stock > 0 AND current_stock <= reorder_threshold")
        low_stock_count = cursor.fetchone()[0]

        # Calculate nearly expiring and expired items based on simulated_time
        sim_dt = datetime.strptime(state["simulated_time"], "%Y-%m-%d %H:%M:%S")
        cursor.execute("SELECT expiry_date, current_stock FROM inventory")
        rows = cursor.fetchall()
        expired_count = 0
        near_expiry_count = 0
        for r in rows:
            exp_dt = datetime.strptime(r["expiry_date"], "%Y-%m-%d")
            days = (exp_dt.date() - sim_dt.date()).days
            if days < 0:
                expired_count += 1
            elif 0 <= days <= 5 and r["current_stock"] > 0:
                near_expiry_count += 1

        cursor.execute("SELECT COUNT(*) FROM purchase_orders WHERE status IN ('PENDING', 'IN_TRANSIT')")
        active_pos = cursor.fetchone()[0]

        conn.close()

    return jsonify({
        "status": "online",
        "simulated_time": state["simulated_time"],
        "is_running": bool(state["is_running"]),
        "sim_speed_multiplier": state["sim_speed_multiplier"],
        "total_sales_count": state["total_sales_count"],
        "total_orders_placed": state["total_orders_placed"],
        "metrics": {
            "total_skus": total_skus,
            "total_units": total_units,
            "inventory_value": inventory_value,
            "out_of_stock_count": out_of_stock_count,
            "low_stock_count": low_stock_count,
            "near_expiry_count": near_expiry_count,
            "expired_count": expired_count,
            "active_purchase_orders": active_pos,
            "total_critical_alerts": out_of_stock_count + expired_count + near_expiry_count + low_stock_count
        }
    })

@app.route("/api/inventory", methods=["GET"])
def get_inventory():
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT simulated_time FROM system_state WHERE id = 1")
        sim_time_str = cursor.fetchone()["simulated_time"]
        sim_dt = datetime.strptime(sim_time_str, "%Y-%m-%d %H:%M:%S")

        cursor.execute("SELECT * FROM inventory ORDER BY rack_id ASC, shelf_level ASC")
        rows = cursor.fetchall()

        items = []
        for r in rows:
            item = dict(r)
            exp_dt = datetime.strptime(item["expiry_date"], "%Y-%m-%d")
            days_left = (exp_dt.date() - sim_dt.date()).days
            item["days_until_expiry"] = days_left
            item["fill_percentage"] = round((item["current_stock"] / item["max_capacity"]) * 100, 1) if item["max_capacity"] > 0 else 0
            
            # Recommended order qty
            deficiency = max(0, item["max_capacity"] - item["current_stock"])
            item["recommended_reorder_qty"] = max(item["min_stock"], deficiency)

            # Effective price after discount
            item["effective_price"] = round(item["unit_price"] * (1 - (item["discount_percent"] / 100.0)), 2)
            items.append(item)

        conn.close()

    return jsonify({"inventory": items, "simulated_time": sim_time_str})

@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    """
    Returns classified reminders and alerts:
    1. no_stock: Stock == 0
    2. low_stock: Stock <= reorder_threshold (with recommended minimum order quantity)
    3. expired: Product past expiry (needs quarantine from rack)
    4. near_expiry: Expires within 5 days (reminder: "Sell these products as soon as possible in that rack!")
    """
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT simulated_time FROM system_state WHERE id = 1")
        sim_time_str = cursor.fetchone()["simulated_time"]
        sim_dt = datetime.strptime(sim_time_str, "%Y-%m-%d %H:%M:%S")

        cursor.execute("SELECT * FROM inventory")
        rows = cursor.fetchall()

        no_stock_alerts = []
        low_stock_alerts = []
        expired_alerts = []
        near_expiry_alerts = []

        for r in rows:
            item = dict(r)
            exp_dt = datetime.strptime(item["expiry_date"], "%Y-%m-%d")
            days_left = (exp_dt.date() - sim_dt.date()).days
            item["days_until_expiry"] = days_left
            item["recommended_reorder_qty"] = max(item["min_stock"], item["max_capacity"] - item["current_stock"])

            # 1. Expired Check
            if days_left < 0:
                expired_alerts.append({
                    **item,
                    "alert_title": f"EXPIRED PRODUCT IN {item['rack_id']}",
                    "alert_type": "EXPIRED",
                    "action_required": f"Product expired {abs(days_left)} days ago! Quarantine and remove immediately from {item['rack_id']}.",
                    "severity": "CRITICAL"
                })

            # 2. Nearly Expiring Check
            elif 0 <= days_left <= 5 and item["current_stock"] > 0:
                near_expiry_alerts.append({
                    **item,
                    "alert_title": f"NEARLY EXPIRING IN {item['rack_id']}",
                    "alert_type": "NEAR_EXPIRY",
                    "action_required": f"Expires in {days_left} day(s)! Sell these products as soon as possible in {item['rack_id']}. Recommend flash clearance discount.",
                    "severity": "HIGH",
                    "days_left": days_left
                })

            # 3. Out of Stock Check
            if item["current_stock"] == 0:
                no_stock_alerts.append({
                    **item,
                    "alert_title": f"NO STOCK ALERT: {item['name']}",
                    "alert_type": "NO_STOCK",
                    "action_required": f"Completely out of stock on {item['rack_id']}. Place urgent purchase order for minimum {item['min_stock']} units.",
                    "severity": "CRITICAL"
                })

            # 4. Low Stock Check
            elif item["current_stock"] <= item["reorder_threshold"]:
                low_stock_alerts.append({
                    **item,
                    "alert_title": f"LOW STOCK REMINDER: {item['name']}",
                    "alert_type": "LOW_STOCK",
                    "action_required": f"Current stock is {item['current_stock']} (reorder point: {item['reorder_threshold']}). Reminded to order minimum {item['recommended_reorder_qty']} units.",
                    "severity": "WARNING"
                })

        conn.close()

    return jsonify({
        "simulated_time": sim_time_str,
        "summary": {
            "no_stock_count": len(no_stock_alerts),
            "low_stock_count": len(low_stock_alerts),
            "expired_count": len(expired_alerts),
            "near_expiry_count": len(near_expiry_alerts),
            "total_action_items": len(no_stock_alerts) + len(low_stock_alerts) + len(expired_alerts) + len(near_expiry_alerts)
        },
        "alerts": {
            "no_stock": no_stock_alerts,
            "low_stock": low_stock_alerts,
            "expired": expired_alerts,
            "near_expiry": near_expiry_alerts
        }
    })

@app.route("/api/order", methods=["POST"])
def place_purchase_order():
    """
    Place an order for buying new stocks.
    Payload:
    - sku: Item SKU
    - quantity: Quantity to order (defaults to recommended order qty)
    - supplier: Optional supplier override
    - instant: If True, restocks immediately without waiting for transit
    """
    data = request.get_json() or {}
    sku = data.get("sku")
    order_qty = int(data.get("quantity", 0))
    supplier_override = data.get("supplier")
    instant = bool(data.get("instant", False))

    if not sku:
        return jsonify({"error": "Item SKU is required"}), 400

    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM inventory WHERE sku = ?", (sku,))
        item = cursor.fetchone()
        if not item:
            conn.close()
            return jsonify({"error": "Item not found"}), 404

        item = dict(item)
        if order_qty <= 0:
            order_qty = max(item["min_stock"], item["max_capacity"] - item["current_stock"])

        supplier = supplier_override or item["supplier_name"]
        unit_cost = item["cost_price"]
        total_cost = round(unit_cost * order_qty, 2)

        # Generate PO number
        po_number = f"PO-{datetime.now(IST).strftime('%m%d%H%M')}-{random.randint(100, 999)}"

        cursor.execute("SELECT simulated_time, total_orders_placed FROM system_state WHERE id = 1")
        state = cursor.fetchone()
        sim_time_str = state["simulated_time"]
        orders_count = state["total_orders_placed"] + 1

        sim_dt = datetime.strptime(sim_time_str, "%Y-%m-%d %H:%M:%S")

        if instant:
            # Immediate Restock
            expected_arrival = sim_time_str
            eta_seconds = 0
            remaining_seconds = 0
            status = "DELIVERED"

            cursor.execute("""
                UPDATE inventory
                SET current_stock = MIN(max_capacity, current_stock + ?),
                    last_updated = ?
                WHERE sku = ?
            """, (order_qty, sim_time_str, sku))

            msg = f"Instant Order {po_number} delivered: Restocked {order_qty} units of '{item['name']}' to {item['rack_id']}."
            severity = "SUCCESS"
        else:
            # Transit simulation: ETA between 10 and 20 seconds
            eta_seconds = random.randint(10, 20)
            remaining_seconds = eta_seconds
            expected_arrival = (sim_dt + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
            status = "PENDING"
            msg = f"Purchase Order {po_number} placed for {order_qty} units of '{item['name']}' (Supplier: {supplier}). Delivery to {item['rack_id']} in ~{eta_seconds}s."
            severity = "INFO"

        cursor.execute("""
            INSERT INTO purchase_orders (
                po_number, sku, item_name, rack_id, quantity, unit_cost, total_cost,
                supplier, status, order_time, expected_arrival, eta_seconds, remaining_seconds
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (po_number, sku, item["name"], item["rack_id"], order_qty, unit_cost, total_cost, supplier, status, sim_time_str, expected_arrival, eta_seconds, remaining_seconds))

        cursor.execute("""
            INSERT INTO activity_logs (timestamp, event_type, severity, message, sku, rack_id)
            VALUES (?, 'PURCHASE_ORDER', ?, ?, ?, ?)
        """, (sim_time_str, severity, msg, sku, item["rack_id"]))

        cursor.execute("UPDATE system_state SET total_orders_placed = ? WHERE id = 1", (orders_count,))

        conn.commit()
        conn.close()

    return jsonify({
        "success": True,
        "message": msg,
        "po_number": po_number,
        "sku": sku,
        "quantity": order_qty,
        "total_cost": total_cost,
        "status": status
    })

@app.route("/api/action/discount", methods=["POST"])
def apply_flash_clearance_discount():
    """
    Apply clearance discount to nearly expiring product to sell ASAP in that rack.
    Payload:
    - sku: Item SKU
    - discount_percent: e.g. 40 (defaults to 40%)
    """
    data = request.get_json() or {}
    sku = data.get("sku")
    discount = float(data.get("discount_percent", 40.0))

    if not sku:
        return jsonify({"error": "Item SKU is required"}), 400

    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM inventory WHERE sku = ?", (sku,))
        item = cursor.fetchone()
        if not item:
            conn.close()
            return jsonify({"error": "Item not found"}), 404

        item = dict(item)
        cursor.execute("SELECT simulated_time FROM system_state WHERE id = 1")
        now_iso = cursor.fetchone()["simulated_time"]

        cursor.execute("""
            UPDATE inventory 
            SET discount_percent = ?, last_updated = ?
            WHERE sku = ?
        """, (discount, now_iso, sku))

        effective_price = round(item["unit_price"] * (1 - (discount / 100.0)), 2)
        msg = f"CLEARANCE ACTIVE: Applied {discount}% discount to '{item['name']}' in {item['rack_id']}. New price: ₹{effective_price:.2f}. Selling ASAP to prevent waste!"

        cursor.execute("""
            INSERT INTO activity_logs (timestamp, event_type, severity, message, sku, rack_id)
            VALUES (?, 'CLEARANCE_DISCOUNT', 'SUCCESS', ?, ?, ?)
        """, (now_iso, msg, sku, item["rack_id"]))

        conn.commit()
        conn.close()

    return jsonify({
        "success": True,
        "message": msg,
        "sku": sku,
        "rack_id": item["rack_id"],
        "discount_percent": discount,
        "effective_price": effective_price
    })

@app.route("/api/action/quarantine", methods=["POST"])
def quarantine_expired_product():
    """
    Quarantine and clear expired stock from the rack.
    Payload:
    - sku: Item SKU
    """
    data = request.get_json() or {}
    sku = data.get("sku")

    if not sku:
        return jsonify({"error": "Item SKU is required"}), 400

    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM inventory WHERE sku = ?", (sku,))
        item = cursor.fetchone()
        if not item:
            conn.close()
            return jsonify({"error": "Item not found"}), 404

        item = dict(item)
        removed_qty = item["current_stock"]

        cursor.execute("SELECT simulated_time FROM system_state WHERE id = 1")
        now_iso = cursor.fetchone()["simulated_time"]

        # Reset stock to 0 and mark status QUARANTINED
        cursor.execute("""
            UPDATE inventory
            SET current_stock = 0, status = 'OUT_OF_STOCK', last_updated = ?
            WHERE sku = ?
        """, (now_iso, sku))

        msg = f"QUARANTINED & REMOVED: {removed_qty} expired units of '{item['name']}' evacuated from {item['rack_id']}. Shelf is now clean."

        cursor.execute("""
            INSERT INTO activity_logs (timestamp, event_type, severity, message, sku, rack_id)
            VALUES (?, 'QUARANTINE', 'WARNING', ?, ?, ?)
        """, (now_iso, msg, sku, item["rack_id"]))

        conn.commit()
        conn.close()

    return jsonify({
        "success": True,
        "message": msg,
        "sku": sku,
        "removed_units": removed_qty,
        "rack_id": item["rack_id"]
    })

@app.route("/api/action/sell", methods=["POST"])
def record_sale():
    """
    Manually record customer sale of an item (e.g. fast clearance selling in that rack).
    Payload:
    - sku: Item SKU
    - quantity: Units sold (default 1)
    """
    data = request.get_json() or {}
    sku = data.get("sku")
    qty = int(data.get("quantity", 1))

    if not sku:
        return jsonify({"error": "Item SKU is required"}), 400

    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM inventory WHERE sku = ?", (sku,))
        item = cursor.fetchone()
        if not item:
            conn.close()
            return jsonify({"error": "Item not found"}), 404

        item = dict(item)
        if item["current_stock"] < qty:
            conn.close()
            return jsonify({"error": f"Insufficient stock ({item['current_stock']} available)"}), 400

        new_stock = item["current_stock"] - qty
        cursor.execute("SELECT simulated_time, total_sales_count FROM system_state WHERE id = 1")
        st = cursor.fetchone()
        now_iso = st["simulated_time"]
        new_sales = st["total_sales_count"] + qty

        cursor.execute("""
            UPDATE inventory SET current_stock = ?, last_updated = ? WHERE sku = ?
        """, (new_stock, now_iso, sku))

        cursor.execute("""
            UPDATE system_state SET total_sales_count = ? WHERE id = 1
        """, (new_sales,))

        msg = f"Direct Sale Recorded: {qty} unit(s) of '{item['name']}' sold from {item['rack_id']}. Remaining: {new_stock}."
        cursor.execute("""
            INSERT INTO activity_logs (timestamp, event_type, severity, message, sku, rack_id)
            VALUES (?, 'SALE', 'INFO', ?, ?, ?)
        """, (now_iso, msg, sku, item["rack_id"]))

        conn.commit()
        conn.close()

    return jsonify({"success": True, "message": msg, "sku": sku, "remaining_stock": new_stock})

@app.route("/api/orders", methods=["GET"])
def get_orders():
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM purchase_orders ORDER BY id DESC LIMIT 50")
        orders = [dict(r) for r in cursor.fetchall()]
        conn.close()
    return jsonify({"orders": orders})

@app.route("/api/logs", methods=["GET"])
def get_logs():
    limit = int(request.args.get("limit", 40))
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT ?", (limit,))
        logs = [dict(r) for r in cursor.fetchall()]
        conn.close()
    return jsonify({"logs": logs})

@app.route("/api/simulation/control", methods=["POST"])
def control_simulation():
    """
    Toggle running state or adjust simulation speed multiplier.
    Payload:
    - is_running: bool
    - multiplier: float (e.g. 1.0, 2.0, 5.0, 10.0)
    """
    data = request.get_json() or {}
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT is_running, sim_speed_multiplier, simulated_time FROM system_state WHERE id = 1")
        row = cursor.fetchone()
        now_iso = row["simulated_time"]

        is_running = data.get("is_running", bool(row["is_running"]))
        multiplier = float(data.get("multiplier", row["sim_speed_multiplier"]))

        cursor.execute("""
            UPDATE system_state 
            SET is_running = ?, sim_speed_multiplier = ? 
            WHERE id = 1
        """, (1 if is_running else 0, multiplier))

        status_txt = "RUNNING" if is_running else "PAUSED"
        msg = f"Continuous monitoring simulation updated: Status={status_txt}, Speed={multiplier}x."

        cursor.execute("""
            INSERT INTO activity_logs (timestamp, event_type, severity, message, sku, rack_id)
            VALUES (?, 'SIM_CONTROL', 'INFO', ?, NULL, 'SYSTEM')
        """, (now_iso, msg))

        conn.commit()
        conn.close()

    return jsonify({"success": True, "is_running": is_running, "multiplier": multiplier, "message": msg})

@app.route("/api/reset", methods=["POST"])
def reset_system():
    init_db(force_reset=True)
    return jsonify({"success": True, "message": "Database and sample dataset reset to default initial state."})

# ==============================================================================
# MAIN RUNNER
# ==============================================================================

if __name__ == "__main__":
    init_db(force_reset=False)

    # Start background continuous monitoring engine
    engine = ContinuousMonitoringEngine(interval_seconds=3.0)
    engine.start()
    print("[SIMS Backend] Continuous Monitoring Smart Inventory Engine started.")
    print("[SIMS Backend] Serving REST API on http://127.0.0.1:5000")

    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
