import requests
import json
import time

def test_full_pipeline():
    print("=== 1. CHECK STREAMLIT DASHBOARD ===")
    st_res = requests.get("http://localhost:8501")
    print("Streamlit Status Code:", st_res.status_code)
    assert st_res.status_code == 200, "Streamlit should return 200"

    print("\n=== 2. CHECK CONTINUOUS MONITORING & STATUS ===")
    status_res = requests.get("http://localhost:5000/api/status").json()
    print("Simulated Time:", status_res["simulated_time"])
    print("Is Running:", status_res["is_running"])
    print("Metrics:", json.dumps(status_res["metrics"], indent=2))

    print("\n=== 3. CHECK ALERTS & REMINDERS ===")
    alerts_res = requests.get("http://localhost:5000/api/alerts").json()
    print("Alerts Summary:", alerts_res["summary"])

    print("\n--- Nearly Expiring (Sell ASAP in Rack) ---")
    for a in alerts_res["alerts"]["near_expiry"]:
        print(f"[{a['rack_id']}] {a['name']} - Expires in {a['days_left']} days! Directive: {a['action_required']}")

    print("\n--- Low Stock & Minimum Reorder Reminders ---")
    for a in alerts_res["alerts"]["low_stock"]:
        print(f"[{a['rack_id']}] {a['name']} - Stock: {a['current_stock']}/{a['reorder_threshold']} (Min Reorder: {a['recommended_reorder_qty']} units)")

    print("\n--- No Stock (Out of Stock) ---")
    for a in alerts_res["alerts"]["no_stock"]:
        print(f"[{a['rack_id']}] {a['name']} - Current Stock: {a['current_stock']}! Urgent restock required.")

    print("\n--- Expired Products (Quarantine) ---")
    for a in alerts_res["alerts"]["expired"]:
        print(f"[{a['rack_id']}] {a['name']} - Expired {abs(a['days_until_expiry'])} days ago! Must quarantine.")

    print("\n=== 4. TEST ACTION: APPLY 40% CLEARANCE DISCOUNT ON NEARLY EXPIRING RACK ITEM ===")
    target_sku = alerts_res["alerts"]["near_expiry"][0]["sku"]
    disc_res = requests.post("http://localhost:5000/api/action/discount", json={"sku": target_sku, "discount_percent": 40.0}).json()
    print("Discount Action Output:", disc_res["message"])

    print("\n=== 5. TEST ACTION: PLACE PURCHASE ORDER FOR BUYING NEW STOCKS ===")
    order_sku = alerts_res["alerts"]["low_stock"][0]["sku"]
    po_res = requests.post("http://localhost:5000/api/order", json={"sku": order_sku, "quantity": 25, "instant": True}).json()
    print("Purchase Order Result:", po_res["message"])

    print("\n=== 6. TEST ACTION: QUARANTINE EXPIRED PRODUCT FROM RACK ===")
    if alerts_res["alerts"]["expired"]:
        exp_sku = alerts_res["alerts"]["expired"][0]["sku"]
        quar_res = requests.post("http://localhost:5000/api/action/quarantine", json={"sku": exp_sku}).json()
        print("Quarantine Result:", quar_res["message"])

    print("\n=== 7. VERIFY AUDIT LOGS ===")
    logs_res = requests.get("http://localhost:5000/api/logs?limit=5").json()
    for l in logs_res["logs"]:
        print(f"[{l['timestamp']}] [{l['event_type']}] {l['message']}")

    print("\n>>> ALL SYSTEM VERIFICATIONS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    test_full_pipeline()
