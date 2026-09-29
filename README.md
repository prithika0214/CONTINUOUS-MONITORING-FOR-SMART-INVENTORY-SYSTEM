# 📦 Continuous Monitoring Smart Inventory System (SIMS)

A real-time, autonomous, smart inventory monitoring and predictive procurement system written in **100% Python**.

---

## 🌟 Architectural Design: Strict 2-File Segregation

Per the project specification, all application logic is cleanly divided into:
1. **`backend.py`**: **All backend code in ONLY ONE file**
   - SQLite persistent database layer with thread-safe connection pooling.
   - Realistic multi-category, multi-rack sample dataset (`Rack A-01` through `Rack F-02`).
   - Background daemon engine (`ContinuousMonitoringEngine`) running continuously.
   - Dynamic store clock, simulated consumer sales consumption, and shelf sensor telemetry.
   - Predictive expiry monitoring and threshold alert classification.
   - Complete REST API with procurement order processing and instant/transit delivery handling.
2. **`frontend.py`**: **All frontend code in ONE file**
   - Executive-grade, modern dashboard powered by Streamlit.
   - Live continuous refresh loop using `@st.fragment(run_every="2s")`.
   - Real-time animated pulse indicator and simulated clock display.
   - **Urgent Action Center**:
     - ⚡ **Nearly Expiring Products**: Warns manager to *"Sell these products as soon as possible in Rack [X]!"* with one-click **"Apply 40% Clearance Discount"**.
     - 📦 **Low Stock & Minimum Reorder Reminders**: Notifies when items drop below safety thresholds with one-click **"1-Click Reorder"**.
     - 🔴 **Out of Stock (No Stock) Alerts**: Highlights empty shelves with urgent reorder actions.
     - 🚫 **Expired Products Quarantine**: Identifies expired stock on shelves with a **"Quarantine & Clear Rack"** button.
   - **Procurement & Purchase Order Placement Desk**: Reorder wizard to calculate costs, select suppliers, and place purchase orders.
   - **Physical Warehouse & Retail Rack Visualizer**: Visual shelf fill meters, temperature/storage classification, and live capacity bars.
   - **Master Inventory Directory**: Multi-criteria search, sorting, and CSV export.
   - **Simulation Engine Controls & Audit Log Stream**: Real-time ticker and rush-hour traffic simulator.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
Ensure Python 3.10+ is installed. Dependencies:
```bash
pip install flask flask-cors requests streamlit pandas
```

### 2. Run the System

You can run the entire system with a single command using the included launcher:
```bash
python run_system.py
```
*This automatically starts the backend API on port 5000 and opens the Streamlit frontend dashboard on port 8501 in your browser.*

Alternatively, you can run each file independently:

**Terminal 1 (Backend):**
```bash
python backend.py
```

**Terminal 2 (Frontend):**
```bash
python -m streamlit run frontend.py
```

- **Dashboard UI**: [http://localhost:8501](http://localhost:8501)
- **Backend API**: [http://localhost:5000](http://localhost:5000)

---

## 📊 Pre-Configured Sample Dataset

| SKU | Product Name | Rack Location | Category | Stock / Cap | Expiry Status | System Directive |
|---|---|---|---|---|---|---|
| `SKU-DAI-101` | Farm Fresh Whole Milk 1L | Rack A-01 | Dairy | 14 / 80 | Near Expiry (2 days) | **Sell ASAP in Rack A-01! Apply Flash Discount!** |
| `SKU-DAI-102` | Artisan Greek Yogurt 500g | Rack A-02 | Dairy | 8 / 50 | Expired (1 day ago) | **Quarantine immediately from Rack A-02!** |
| `SKU-BAK-201` | Rustic Sourdough Loaf | Rack B-01 | Bakery | 18 / 40 | Near Expiry (3 days) | **Sell ASAP in Rack B-01! Apply Clearance!** |
| `SKU-PRD-202` | Organic Cavendish Bananas 1kg | Rack B-02 | Produce | 4 / 60 | Low Stock (Min: 20) | **Order minimum stock (25 units) now!** |
| `SKU-MED-301` | Pain Relief Ibuprofen 200mg | Rack C-01 | Pharmacy | 45 / 70 | Healthy | Normal monitoring |
| `SKU-MED-302` | Antibacterial Hand Sanitizer | Rack C-02 | Pharmacy | 0 / 100 | Out of Stock | **Emergency replenishment order needed!** |
| `SKU-BEV-401` | Cold Pressed Orange Juice 750ml | Rack D-01 | Beverages | 5 / 50 | Low Stock & Near Expiry | **Dual Alert: Restock & Sell Remaining ASAP!** |
| `SKU-BEV-402` | Sparkling Spring Water 12x330ml | Rack D-02 | Beverages | 65 / 90 | Healthy | Normal monitoring |
| `SKU-PAN-501` | Wild Albacore Canned Tuna 180g | Rack E-01 | Pantry | 110 / 150 | Healthy | Normal monitoring |
| `SKU-PAN-502` | Organic Basil Pasta Sauce 500ml | Rack E-02 | Pantry | 7 / 80 | Low Stock (Min: 25) | **Order minimum stock now!** |
| `SKU-FRZ-601` | Frozen Wild Berry Blend 1kg | Rack F-01 | Frozen | 6 / 60 | Low Stock (Min: 20) | **Order minimum stock now!** |
| `SKU-FRZ-602` | Madagascar Vanilla Ice Cream 1L | Rack F-02 | Frozen | 34 / 60 | Healthy | Normal monitoring |

---

## 🛠️ REST API Endpoints (`backend.py`)

- `GET /api/status`: System state, simulated clock, and top-level KPI metrics.
- `GET /api/inventory`: Full inventory list with computed urgency flags, days-to-expiry, and rack locations.
- `GET /api/alerts`: Classified reminder lists (`near_expiry`, `low_stock`, `no_stock`, `expired`).
- `POST /api/order`: Dispatch purchase orders for new stock (`sku`, `quantity`, `supplier`, `instant`).
- `POST /api/action/discount`: Apply flash clearance discount (e.g., 40%) to nearly expiring rack products.
- `POST /api/action/quarantine`: Quarantine expired items off the rack.
- `POST /api/action/sell`: Record direct sale from rack.
- `GET /api/orders`: Live tracking of active and historical purchase orders.
- `POST /api/simulation/control`: Pause/resume and change simulation clock multiplier.
- `POST /api/reset`: Reset SQLite database to pristine sample dataset.
- `GET /api/logs`: Audit trail of all telemetry, sales, alerts, and replenishment events.

---

## 🐳 Docker Deployment

To run the entire system using Docker Compose:

1. Ensure Docker is installed and running.
2. Build and start the services:
   `ash
   docker-compose up --build
   `
3. Access the Flask App at [http://localhost:5000](http://localhost:5000)
4. Access the Streamlit Dashboard at [http://localhost:8501](http://localhost:8501)

## 🔄 Updating to the Indian Grocery Dataset

The system was updated to remove old demo content and integrate the Indian grocery dataset. 
* All prices are now displayed in INR (₹) instead of $.
* Timezones are hardcoded to IST (Indian Standard Time).
* Old demo laptops/keyboards were removed.
* A controlled reset script is provided:
  `ash
  python scripts/reset_inventory.py
  `

### DevOps & Automation
* Docker and docker-compose.yml configured.
* GitHub Actions CI workflow created at .github/workflows/ci.yml.

