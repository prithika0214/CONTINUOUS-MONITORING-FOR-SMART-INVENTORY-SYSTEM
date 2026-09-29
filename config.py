import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database", "inventory.db")
DATA_CSV = os.path.join(BASE_DIR, "data", "stockpulse_indian_grocery_dataset.csv")
MODEL_PATH = os.path.join(BASE_DIR, "ml", "inventory_demand_model.pkl")

SECRET_KEY = os.environ.get("STOCKPULSE_SECRET_KEY", "local-development-only-change-me")
MONITORING_INTERVAL = 4