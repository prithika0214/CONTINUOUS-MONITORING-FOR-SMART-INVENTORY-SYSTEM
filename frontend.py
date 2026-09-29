"""
Continuous Monitoring Smart Inventory System - Frontend Dashboard
All frontend UI and interaction code encapsulated in this single 100% Python file.
Powered by Streamlit with continuous live fragment monitoring.
"""

import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
from zoneinfo import ZoneInfo
IST = ZoneInfo('Asia/Kolkata')

# ==============================================================================
# CONFIGURATION & STYLING
# ==============================================================================

st.set_page_config(
    page_title="Smart Inventory Monitoring System",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

BACKEND_URL = "http://127.0.0.1:5000"

# Inject custom modern enterprise CSS
st.markdown("""
<style>
    /* Global Polish */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }
    
    /* Header & Pulse */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 1.2rem 1.8rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    }
    
    .pulse-dot {
        display: inline-block;
        width: 12px;
        height: 12px;
        background-color: #10b981;
        border-radius: 50%;
        margin-right: 8px;
        box-shadow: 0 0 10px #10b981;
        animation: pulse 1.8s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1.1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    
    /* KPI Card Styles */
    .kpi-card {
        background: #1e293b;
        border-radius: 10px;
        padding: 1.1rem;
        border: 1px solid rgba(255, 255, 255, 0.06);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        text-align: center;
    }
    .kpi-title {
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        margin-bottom: 0.3rem;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f8fafc;
    }
    
    /* Action Alert Cards */
    .alert-card-danger {
        background: rgba(239, 68, 68, 0.12);
        border-left: 5px solid #ef4444;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.9rem;
    }
    
    .alert-card-warning {
        background: rgba(245, 158, 11, 0.12);
        border-left: 5px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.9rem;
    }
    
    .alert-card-orange {
        background: rgba(249, 115, 22, 0.15);
        border-left: 5px solid #f97316;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.9rem;
    }
    
    .alert-card-blue {
        background: rgba(59, 130, 246, 0.12);
        border-left: 5px solid #3b82f6;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.9rem;
    }

    /* Rack Visual Card */
    .rack-card {
        background: #1e293b;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
        transition: transform 0.2s ease;
    }
    .rack-card:hover {
        transform: translateY(-2px);
        border-color: rgba(59, 130, 246, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# API HELPER FUNCTIONS
# ==============================================================================

def api_get(endpoint):
    try:
        res = requests.get(f"{BACKEND_URL}{endpoint}", timeout=4)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        return None
    return None

def api_post(endpoint, payload=None):
    try:
        res = requests.post(f"{BACKEND_URL}{endpoint}", json=payload or {}, timeout=4)
        if res.status_code == 200:
            return res.json()
        else:
            return {"error": res.text, "status_code": res.status_code}
    except Exception as e:
        return {"error": str(e)}

# ==============================================================================
# LIVE MONITORING FRAGMENT (Auto-refreshes every 2 seconds)
# ==============================================================================

@st.fragment(run_every="2s")
def render_live_monitoring_fragment():
    status_data = api_get("/api/status")
    alerts_data = api_get("/api/alerts")
    inv_data = api_get("/api/inventory")

    if not status_data or not alerts_data or not inv_data:
        st.error("⚠️ Unable to connect to Smart Inventory Backend on http://127.0.0.1:5000. Please ensure `python backend.py` is running.")
        if st.button("🔄 Retry Connection"):
            st.rerun()
        return

    sim_time = status_data.get("simulated_time", "N/A")
    metrics = status_data.get("metrics", {})
    is_running = status_data.get("is_running", True)
    speed_mult = status_data.get("sim_speed_multiplier", 1.0)
    alerts = alerts_data.get("alerts", {})
    summary = alerts_data.get("summary", {})
    inventory = inv_data.get("inventory", [])

    # 1. Top Real-Time Status & Clock Banner
    pulse_color = "#10b981" if is_running else "#f59e0b"
    status_label = f"LIVE CONTINUOUS MONITORING ACTIVE ({speed_mult}x)" if is_running else "MONITORING PAUSED"

    col_h1, col_h2 = st.columns([3, 2])
    with col_h1:
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            <span class="pulse-dot" style="background-color: {pulse_color}; box-shadow: 0 0 10px {pulse_color};"></span>
            <span style="font-size: 1.1rem; font-weight: 700; letter-spacing: 0.04em; color: #f8fafc;">
                {status_label}
            </span>
        </div>
        <div style="color: #94a3b8; font-size: 0.88rem;">
            Autonomous Telemetry &bull; Shelf Level Sensors &bull; Dynamic Expiry Prediction Engine
        </div>
        """, unsafe_allow_html=True)

    with col_h2:
        st.markdown(f"""
        <div style="text-align: right; background: rgba(30, 41, 59, 0.7); padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);">
            <div style="font-size: 0.75rem; text-transform: uppercase; color: #94a3b8; font-weight: 600;">Simulated Store Clock</div>
            <div style="font-size: 1.25rem; font-weight: 800; color: #38bdf8; font-family: monospace;">⏱️ {sim_time}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='margin: 0.8rem 0; border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

    # 2. Executive KPI Metrics Bar
    k1, k2, k3, k4, k5, k6, k7 = st.columns(7)
    with k1:
        st.metric("Total SKUs", metrics.get("total_skus", 0), delta=f"{metrics.get('total_units', 0)} Units")
    with k2:
        st.metric("Valuation", f"₹{metrics.get('inventory_value', 0.0):,.2f}")
    with k3:
        out_cnt = metrics.get("out_of_stock_count", 0)
        st.metric("No Stock", out_cnt, delta="Critical" if out_cnt > 0 else "Clear", delta_color="inverse")
    with k4:
        low_cnt = metrics.get("low_stock_count", 0)
        st.metric("Low Stock", low_cnt, delta="Reorder Needed" if low_cnt > 0 else "OK", delta_color="inverse")
    with k5:
        near_cnt = metrics.get("near_expiry_count", 0)
        st.metric("Near Expiry", near_cnt, delta="Sell ASAP" if near_cnt > 0 else "OK", delta_color="inverse")
    with k6:
        exp_cnt = metrics.get("expired_count", 0)
        st.metric("Expired", exp_cnt, delta="Quarantine" if exp_cnt > 0 else "Zero", delta_color="inverse")
    with k7:
        st.metric("Active POs", metrics.get("active_purchase_orders", 0), delta="In Transit")

    st.markdown("<br>", unsafe_allow_html=True)

    # ==============================================================================
    # 3. URGENT ACTION & CONTINUOUS REMINDER CENTER (The Core Requirements)
    # ==============================================================================
    st.markdown("### 🚨 Urgent Action & Continuous Reminders Center")
    st.caption("Live alerts stream automatically updated by the background continuous monitoring engine.")

    # Tabs for distinct reminder categories
    tab_exp, tab_low, tab_zero, tab_quar = st.tabs([
        f"⚡ Nearly Expiring (Sell ASAP) [{summary.get('near_expiry_count', 0)}]",
        f"📦 Low Stock & Reorders [{summary.get('low_stock_count', 0)}]",
        f"🔴 Out of Stock (No Stock) [{summary.get('no_stock_count', 0)}]",
        f"🚫 Expired Products [{summary.get('expired_count', 0)}]"
    ])

    # --------------------------------------------------------------------------
    # TAB 1: NEARLY EXPIRING PRODUCTS - TELL US TO SELL ASAP IN THAT RACK
    # --------------------------------------------------------------------------
    with tab_exp:
        near_list = alerts.get("near_expiry", [])
        if not near_list:
            st.success("✅ Excellent! No products are currently nearing expiration.")
        else:
            st.markdown("""
            <div style="background: rgba(249, 115, 22, 0.15); border: 1px solid #f97316; border-radius: 8px; padding: 0.8rem 1.2rem; margin-bottom: 1rem;">
                <b style="color: #f97316; font-size: 1rem;">⚠️ CRITICAL INVENTORY DIRECTIVE:</b>
                <span style="color: #fed7aa; margin-left: 8px;">
                    The continuous monitoring system has detected perishable products nearing expiration. 
                    <b>Sell these products as soon as possible in their designated racks!</b> Apply flash clearance discounts or push sales immediately to prevent shrinkage.
                </span>
            </div>
            """, unsafe_allow_html=True)

            for item in near_list:
                days = item.get("days_left", 0)
                orig_price = item["unit_price"]
                disc = item.get("discount_percent", 0.0)
                eff_price = round(orig_price * (1 - (disc / 100.0)), 2)

                col_a, col_b, col_c, col_d = st.columns([3, 2, 2, 2])
                with col_a:
                    st.markdown(f"""
                    <div style="font-weight: 700; font-size: 1.05rem; color: #f8fafc;">{item['name']}</div>
                    <div style="color: #94a3b8; font-size: 0.85rem;">
                        SKU: <code>{item['sku']}</code> &bull; Batch: <code>{item['batch_no']}</code> &bull; Category: <b>{item['category']}</b>
                    </div>
                    <div style="color: #fb923c; font-weight: 600; font-size: 0.9rem; margin-top: 4px;">
                        📍 Location: <b>{item['rack_id']}</b> &bull; {item['shelf_level']}
                    </div>
                    """, unsafe_allow_html=True)

                with col_b:
                    st.markdown(f"""
                    <div style="font-size: 0.82rem; color: #94a3b8;">TIME REMAINING</div>
                    <div style="color: #f97316; font-size: 1.2rem; font-weight: 800;">⏳ {days} Day(s) Left</div>
                    <div style="font-size: 0.82rem; color: #94a3b8;">Expires: {item['expiry_date']}</div>
                    <div style="font-size: 0.85rem; color: #e2e8f0;">Stock in Rack: <b>{item['current_stock']} units</b></div>
                    """, unsafe_allow_html=True)

                with col_c:
                    if disc > 0:
                        st.markdown(f"""
                        <div style="font-size: 0.82rem; color: #10b981; font-weight: 700;">🔥 CLEARANCE APPLIED: {disc:.0f}% OFF</div>
                        <div style="font-size: 1.25rem; font-weight: 800; color: #4ade80;">₹{eff_price:.2f} <s style="font-size: 0.85rem; color: #94a3b8;">₹{orig_price:.2f}</s></div>
                        <div style="font-size: 0.8rem; color: #a7f3d0;">Selling fast in {item['rack_id']}!</div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="font-size: 0.82rem; color: #94a3b8;">CURRENT PRICE</div>
                        <div style="font-size: 1.25rem; font-weight: 800; color: #f8fafc;">₹{orig_price:.2f}</div>
                        <div style="font-size: 0.8rem; color: #f87171;">Full Price (No Discount)</div>
                        """, unsafe_allow_html=True)

                with col_d:
                    # Quick action buttons
                    if disc == 0:
                        if st.button(f"⚡ Apply 40% Clearance Discount", key=f"disc_{item['sku']}"):
                            res = api_post("/api/action/discount", {"sku": item["sku"], "discount_percent": 40.0})
                            if "success" in res:
                                st.success(f"40% Discount applied to {item['rack_id']}!")
                                st.rerun()
                    else:
                        if st.button(f"🛒 Quick Sell 2 Units in {item['rack_id']}", key=f"sell_{item['sku']}"):
                            res = api_post("/api/action/sell", {"sku": item["sku"], "quantity": 2})
                            if "success" in res:
                                st.toast(f"Sold 2 units of {item['name']} from {item['rack_id']}!")
                                st.rerun()

                st.markdown("<hr style='margin: 0.5rem 0; border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # TAB 2: LOW STOCK & MINIMUM REORDER REMINDERS
    # --------------------------------------------------------------------------
    with tab_low:
        low_list = alerts.get("low_stock", [])
        if not low_list:
            st.success("✅ All stock levels are currently above minimum safety thresholds.")
        else:
            st.markdown("""
            <div style="background: rgba(245, 158, 11, 0.12); border: 1px solid #f59e0b; border-radius: 8px; padding: 0.8rem 1.2rem; margin-bottom: 1rem;">
                <b style="color: #f59e0b; font-size: 1rem;">⚠️ LOW STOCK REORDER DIRECTIVE:</b>
                <span style="color: #fde68a; margin-left: 8px;">
                    Stock levels have fallen below safety reorder thresholds! 
                    <b>Reminded to order minimum stocks immediately</b> to maintain shelf availability and prevent stockouts.
                </span>
            </div>
            """, unsafe_allow_html=True)

            for item in low_list:
                rec_order = item.get("recommended_reorder_qty", item["min_stock"])
                col_l1, col_l2, col_l3, col_l4 = st.columns([3, 2, 2, 2])

                with col_l1:
                    st.markdown(f"""
                    <div style="font-weight: 700; font-size: 1.05rem; color: #f8fafc;">{item['name']}</div>
                    <div style="color: #94a3b8; font-size: 0.85rem;">
                        SKU: <code>{item['sku']}</code> &bull; Rack: <b>{item['rack_id']}</b> ({item['shelf_level']})
                    </div>
                    <div style="color: #cbd5e1; font-size: 0.85rem; margin-top: 3px;">
                        Supplier: <b>{item['supplier_name']}</b>
                    </div>
                    """, unsafe_allow_html=True)

                with col_l2:
                    st.markdown(f"""
                    <div style="font-size: 0.82rem; color: #94a3b8;">STOCK STATUS</div>
                    <div style="color: #f59e0b; font-size: 1.2rem; font-weight: 800;">⚠️ {item['current_stock']} Units Left</div>
                    <div style="font-size: 0.82rem; color: #94a3b8;">
                        Min Stock: {item['min_stock']} | Reorder Point: {item['reorder_threshold']}
                    </div>
                    """, unsafe_allow_html=True)

                with col_l3:
                    est_cost = rec_order * item["cost_price"]
                    st.markdown(f"""
                    <div style="font-size: 0.82rem; color: #94a3b8;">RECOMMENDED REORDER</div>
                    <div style="font-size: 1.2rem; font-weight: 800; color: #38bdf8;">📦 {rec_order} Units</div>
                    <div style="font-size: 0.82rem; color: #94a3b8;">Unit Cost: ₹{item['cost_price']:.2f} (Total: ₹{est_cost:.2f})</div>
                    """, unsafe_allow_html=True)

                with col_l4:
                    if st.button(f"🚀 1-Click Reorder ({rec_order} Units)", key=f"reorder_{item['sku']}"):
                        res = api_post("/api/order", {
                            "sku": item["sku"],
                            "quantity": rec_order,
                            "instant": False
                        })
                        if "success" in res:
                            st.toast(f"PO Placed for {rec_order} units of {item['name']}!")
                            st.rerun()

                st.markdown("<hr style='margin: 0.5rem 0; border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # TAB 3: OUT OF STOCK (NO STOCK) REMINDERS
    # --------------------------------------------------------------------------
    with tab_zero:
        zero_list = alerts.get("no_stock", [])
        if not zero_list:
            st.success("✅ Zero stockouts! Every SKU has available inventory.")
        else:
            st.markdown("""
            <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid #ef4444; border-radius: 8px; padding: 0.8rem 1.2rem; margin-bottom: 1rem;">
                <b style="color: #ef4444; font-size: 1rem;">🚨 URGENT: NO STOCK / OUT OF STOCK DETECTED:</b>
                <span style="color: #fecaca; margin-left: 8px;">
                    Racks are empty for the following items! Customers cannot purchase these products. 
                    <b>Place emergency replenishment orders immediately!</b>
                </span>
            </div>
            """, unsafe_allow_html=True)

            for item in zero_list:
                rec_order = item.get("recommended_reorder_qty", item["min_stock"])
                col_z1, col_z2, col_z3, col_z4 = st.columns([3, 2, 2, 2])

                with col_z1:
                    st.markdown(f"""
                    <div style="font-weight: 700; font-size: 1.05rem; color: #f8fafc;">{item['name']}</div>
                    <div style="color: #94a3b8; font-size: 0.85rem;">
                        SKU: <code>{item['sku']}</code> &bull; Location: <b>{item['rack_id']}</b> ({item['shelf_level']})
                    </div>
                    <div style="color: #ef4444; font-weight: 700; font-size: 0.9rem; margin-top: 3px;">
                        EMPTY SHELF ON {item['rack_id']}
                    </div>
                    """, unsafe_allow_html=True)

                with col_z2:
                    st.markdown(f"""
                    <div style="font-size: 0.82rem; color: #94a3b8;">CURRENT STOCK</div>
                    <div style="color: #ef4444; font-size: 1.3rem; font-weight: 800;">🔴 0 UNITS</div>
                    <div style="font-size: 0.82rem; color: #94a3b8;">Min Safety Target: {item['min_stock']} units</div>
                    """, unsafe_allow_html=True)

                with col_z3:
                    cost = rec_order * item["cost_price"]
                    st.markdown(f"""
                    <div style="font-size: 0.82rem; color: #94a3b8;">URGENT RESTOCK REQ.</div>
                    <div style="font-size: 1.2rem; font-weight: 800; color: #38bdf8;">📦 {rec_order} Units</div>
                    <div style="font-size: 0.82rem; color: #94a3b8;">Supplier: {item['supplier_name']}</div>
                    """, unsafe_allow_html=True)

                with col_z4:
                    if st.button(f"⚡ Instant Restock ({rec_order} Units)", key=f"inst_{item['sku']}"):
                        res = api_post("/api/order", {
                            "sku": item["sku"],
                            "quantity": rec_order,
                            "instant": True
                        })
                        if "success" in res:
                            st.success(f"Restocked {rec_order} units of {item['name']} on {item['rack_id']}!")
                            st.rerun()

                st.markdown("<hr style='margin: 0.5rem 0; border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # TAB 4: EXPIRED PRODUCTS QUARANTINE
    # --------------------------------------------------------------------------
    with tab_quar:
        exp_list = alerts.get("expired", [])
        if not exp_list:
            st.success("✅ Clean shelves! Zero expired products detected on any rack.")
        else:
            st.markdown("""
            <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid #ef4444; border-radius: 8px; padding: 0.8rem 1.2rem; margin-bottom: 1rem;">
                <b style="color: #ef4444; font-size: 1rem;">🚫 HEALTH & SAFETY HAZARD - EXPIRED ITEMS:</b>
                <span style="color: #fecaca; margin-left: 8px;">
                    The following items have passed their expiration date! 
                    <b>Quarantine and evacuate them from their racks immediately to prevent accidental customer purchase!</b>
                </span>
            </div>
            """, unsafe_allow_html=True)

            for item in exp_list:
                days_over = abs(item.get("days_until_expiry", 0))
                col_e1, col_e2, col_e3, col_e4 = st.columns([3, 2, 2, 2])

                with col_e1:
                    st.markdown(f"""
                    <div style="font-weight: 700; font-size: 1.05rem; color: #f8fafc;">{item['name']}</div>
                    <div style="color: #94a3b8; font-size: 0.85rem;">
                        SKU: <code>{item['sku']}</code> &bull; Batch: <code>{item['batch_no']}</code>
                    </div>
                    <div style="color: #ef4444; font-weight: 700; font-size: 0.9rem; margin-top: 3px;">
                        🚨 ON DISPLAY IN: <b>{item['rack_id']}</b> ({item['shelf_level']})
                    </div>
                    """, unsafe_allow_html=True)

                with col_e2:
                    st.markdown(f"""
                    <div style="font-size: 0.82rem; color: #94a3b8;">EXPIRY STATUS</div>
                    <div style="color: #ef4444; font-size: 1.15rem; font-weight: 800;">❌ Expired {days_over} Day(s) Ago</div>
                    <div style="font-size: 0.82rem; color: #94a3b8;">Expiry Date: {item['expiry_date']}</div>
                    """, unsafe_allow_html=True)

                with col_e3:
                    st.markdown(f"""
                    <div style="font-size: 0.82rem; color: #94a3b8;">UNITS COMPROMISED</div>
                    <div style="font-size: 1.2rem; font-weight: 800; color: #cbd5e1;">{item['current_stock']} Units on Shelf</div>
                    <div style="font-size: 0.82rem; color: #f87171;">Cannot be sold. Write-off required.</div>
                    """, unsafe_allow_html=True)

                with col_e4:
                    if st.button(f"🧹 Quarantine & Clear Rack", key=f"quar_{item['sku']}"):
                        res = api_post("/api/action/quarantine", {"sku": item["sku"]})
                        if "success" in res:
                            st.success(f"Quarantined {item['name']} from {item['rack_id']}!")
                            st.rerun()

                st.markdown("<hr style='margin: 0.5rem 0; border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ==============================================================================
    # 4. SMART PURCHASE ORDER PLACEMENT DESK ("place the order for buying the new stocks")
    # ==============================================================================
    st.markdown("### 🛒 Stock Procurement & Purchase Order Placement Desk")
    st.caption("Generate, dispatch, and track orders for buying new inventory from suppliers.")

    with st.expander("📝 Open Purchase Order Creation Form", expanded=False):
        sku_options = [f"{item['sku']} - {item['name']} ({item['rack_id']})" for item in inventory]
        selected_sku_str = st.selectbox("Select Product to Order", sku_options)

        if selected_sku_str:
            sel_sku = selected_sku_str.split(" - ")[0]
            sel_item = next((x for x in inventory if x["sku"] == sel_sku), None)

            if sel_item:
                p_c1, p_c2, p_c3 = st.columns(3)
                with p_c1:
                    st.info(f"""
                    **Item:** {sel_item['name']}  
                    **Rack:** {sel_item['rack_id']} ({sel_item['shelf_level']})  
                    **Current Stock:** {sel_item['current_stock']} / {sel_item['max_capacity']} units  
                    **Min Safety Stock:** {sel_item['min_stock']} units
                    """)
                with p_c2:
                    default_qty = sel_item.get("recommended_reorder_qty", sel_item["min_stock"])
                    order_qty = st.number_input(
                        "Order Quantity (Units)",
                        min_value=1,
                        max_value=max(200, sel_item["max_capacity"]),
                        value=default_qty,
                        step=5
                    )
                    supplier_name = st.text_input("Supplier", value=sel_item["supplier_name"])
                with p_c3:
                    unit_c = sel_item["cost_price"]
                    tot_c = order_qty * unit_c
                    st.metric("Total Order Cost", f"₹{tot_c:,.2f}", delta=f"₹{unit_c:.2f} per unit")
                    is_instant = st.checkbox("⚡ Priority Air Express (Immediate Restock Arrival)", value=False)

                    if st.button("🚀 Confirm & Dispatch Purchase Order", type="primary", use_container_width=True):
                        res = api_post("/api/order", {
                            "sku": sel_sku,
                            "quantity": order_qty,
                            "supplier": supplier_name,
                            "instant": is_instant
                        })
                        if "success" in res:
                            st.success(f"Successfully placed Purchase Order #{res['po_number']}! Total: ₹{tot_c:,.2f}")
                            st.rerun()

    # Active Purchase Orders Live Tracker
    orders_data = api_get("/api/orders")
    if orders_data and orders_data.get("orders"):
        st.markdown("##### 📦 Live Purchase Orders Tracking")
        po_list = orders_data["orders"][:8]
        po_rows = []
        for po in po_list:
            status_icon = "🚚 In Transit" if po["status"] == "IN_TRANSIT" else ("⏳ Processing" if po["status"] == "PENDING" else "✅ Delivered & Restocked")
            po_rows.append({
                "PO Number": po["po_number"],
                "Item": po["item_name"],
                "Destination Rack": po["rack_id"],
                "Quantity": f"{po['quantity']} units",
                "Total Cost": f"₹{po['total_cost']:.2f}",
                "Supplier": po["supplier"],
                "Status": status_icon,
                "ETA Remaining": f"{po['remaining_seconds']}s" if po["status"] in ("PENDING", "IN_TRANSIT") else "Arrived",
                "Order Time": po["order_time"]
            })
        st.dataframe(pd.DataFrame(po_rows), use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ==============================================================================
    # 5. INTERACTIVE PHYSICAL RACK & SHELF VISUALIZER
    # ==============================================================================
    st.markdown("### 🏬 Physical Warehouse & Retail Rack Visualizer")
    st.caption("Continuous telemetry monitoring shelf capacity, rack storage status, and expiration countdowns.")

    # Group inventory by Rack ID
    rack_groups = {}
    for item in inventory:
        r_id = item["rack_id"]
        if r_id not in rack_groups:
            rack_groups[r_id] = []
        rack_groups[r_id].append(item)

    # Display racks in 3 columns
    rack_cols = st.columns(3)
    rack_keys = sorted(rack_groups.keys())

    for idx, r_id in enumerate(rack_keys):
        items = rack_groups[r_id]
        with rack_cols[idx % 3]:
            with st.container():
                for itm in items:
                    pct = itm["fill_percentage"]
                    status = itm["status"]
                    days = itm.get("days_until_expiry", 999)

                    # Determine color border
                    if status == "EXPIRED":
                        border_col = "#ef4444"
                        badge_txt = "🚫 EXPIRED"
                        badge_bg = "rgba(239, 68, 68, 0.2)"
                    elif status == "OUT_OF_STOCK":
                        border_col = "#dc2626"
                        badge_txt = "🔴 NO STOCK"
                        badge_bg = "rgba(220, 38, 38, 0.2)"
                    elif status == "NEAR_EXPIRY":
                        border_col = "#f97316"
                        badge_txt = f"⏳ EXP IN {days}D (SELL ASAP!)"
                        badge_bg = "rgba(249, 115, 22, 0.2)"
                    elif status == "LOW_STOCK":
                        border_col = "#f59e0b"
                        badge_txt = "⚠️ LOW STOCK"
                        badge_bg = "rgba(245, 158, 11, 0.2)"
                    else:
                        border_col = "#10b981"
                        badge_txt = "✅ HEALTHY"
                        badge_bg = "rgba(16, 185, 129, 0.2)"

                    st.markdown(f"""
                    <div style="background: #1e293b; border: 1px solid {border_col}; border-radius: 8px; padding: 0.9rem; margin-bottom: 0.8rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <span style="font-weight: 800; color: #38bdf8; font-size: 0.95rem;">📍 {itm['rack_id']} &bull; {itm['shelf_level']}</span>
                            <span style="background: {badge_bg}; color: {border_col}; font-weight: 700; font-size: 0.72rem; padding: 2px 8px; border-radius: 4px; border: 1px solid {border_col};">
                                {badge_txt}
                            </span>
                        </div>
                        <div style="font-size: 1rem; font-weight: 700; color: #f8fafc; margin-bottom: 2px;">{itm['name']}</div>
                        <div style="font-size: 0.8rem; color: #94a3b8; margin-bottom: 6px;">
                            Category: {itm['category']} &bull; Price: ₹{itm['effective_price']:.2f}
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #cbd5e1; margin-bottom: 2px;">
                            <span>Fill Level: {itm['current_stock']} / {itm['max_capacity']} units</span>
                            <span><b>{pct:.1f}%</b></span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.progress(min(1.0, max(0.0, pct / 100.0)))

    st.markdown("<br>", unsafe_allow_html=True)

    # ==============================================================================
    # 6. FULL MASTER INVENTORY TABLE
    # ==============================================================================
    st.markdown("### 📋 Master Inventory Directory")
    st.caption("Real-time table of all warehouse & retail items with sorting, search, and CSV export.")

    search_query = st.text_input("🔍 Search by SKU, Item Name, Category, or Rack...", "")

    # Filter data
    df_raw = pd.DataFrame(inventory)
    if not df_raw.empty:
        if search_query:
            mask = (
                df_raw["sku"].str.contains(search_query, case=False, na=False) |
                df_raw["name"].str.contains(search_query, case=False, na=False) |
                df_raw["category"].str.contains(search_query, case=False, na=False) |
                df_raw["rack_id"].str.contains(search_query, case=False, na=False)
            )
            df_filtered = df_raw[mask]
        else:
            df_filtered = df_raw

        display_df = df_filtered[[
            "sku", "name", "category", "rack_id", "shelf_level",
            "current_stock", "min_stock", "reorder_threshold", "max_capacity",
            "effective_price", "expiry_date", "days_until_expiry", "status", "supplier_name"
        ]].copy()

        display_df.rename(columns={
            "sku": "SKU",
            "name": "Product Name",
            "category": "Category",
            "rack_id": "Rack ID",
            "shelf_level": "Shelf",
            "current_stock": "Current Stock",
            "min_stock": "Min Stock",
            "reorder_threshold": "Reorder Level",
            "max_capacity": "Capacity",
            "effective_price": "Price (₹)",
            "expiry_date": "Expiry Date",
            "days_until_expiry": "Days Left",
            "status": "System Status",
            "supplier_name": "Supplier"
        }, inplace=True)

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Master Inventory CSV",
            data=csv,
            file_name=f"smart_inventory_report_{datetime.now(IST).strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ==============================================================================
    # 7. CONTINUOUS SIMULATION CONTROLS & AUDIT EVENT FEED
    # ==============================================================================
    st.markdown("### ⚙️ Simulation Engine Controls & Audit Trail")
    st.caption("Test the continuous dynamic updates, time acceleration, and inspect live system logs.")

    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns(4)

    with ctrl_col1:
        new_speed = st.selectbox(
            "Simulated Clock Speed",
            [1.0, 2.0, 5.0, 10.0],
            index=[1.0, 2.0, 5.0, 10.0].index(speed_mult) if speed_mult in [1.0, 2.0, 5.0, 10.0] else 0
        )
        if new_speed != speed_mult:
            api_post("/api/simulation/control", {"multiplier": new_speed})
            st.toast(f"Simulation speed updated to {new_speed}x")
            st.rerun()

    with ctrl_col2:
        btn_label = "⏸️ Pause Simulation" if is_running else "▶️ Resume Simulation"
        if st.button(btn_label, use_container_width=True):
            api_post("/api/simulation/control", {"is_running": not is_running})
            st.rerun()

    with ctrl_col3:
        if st.button("👥 Simulate Customer Rush Hour", use_container_width=True):
            # Sell random items to simulate peak traffic
            available = [i for i in inventory if i["current_stock"] > 0 and i["status"] != "EXPIRED"]
            if available:
                import random
                sampled = random.sample(available, min(len(available), 3))
                for s in sampled:
                    api_post("/api/action/sell", {"sku": s["sku"], "quantity": random.randint(2, 4)})
                st.toast("Simulated peak shopping rush! Stock depleted across active racks.")
                st.rerun()

    with ctrl_col4:
        if st.button("🔄 Reset Sample Dataset", use_container_width=True):
            api_post("/api/reset")
            st.toast("System reset to pristine initial sample dataset.")
            st.rerun()

    # Live Audit Logs
    logs_data = api_get("/api/logs?limit=15")
    if logs_data and logs_data.get("logs"):
        st.markdown("##### 📜 Live System Audit & Telemetry Log")
        log_items = logs_data["logs"]
        log_rows = []
        for l in log_items:
            log_rows.append({
                "Timestamp": l["timestamp"],
                "Event": l["event_type"],
                "Severity": l["severity"],
                "Rack": l["rack_id"] or "ALL",
                "Description": l["message"]
            })
        st.dataframe(pd.DataFrame(log_rows), use_container_width=True, hide_index=True)


# ==============================================================================
# MAIN PAGE ENTRYPOINT
# ==============================================================================

def main():
    # Render the continuous live monitoring fragment
    render_live_monitoring_fragment()

if __name__ == "__main__":
    main()
