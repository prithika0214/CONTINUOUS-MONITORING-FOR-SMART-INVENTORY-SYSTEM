from flask import Flask
from flask_cors import CORS

from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.user import user_bp
from routes.inventory import inventory_bp
from routes.transaction import transaction_bp
from routes.suppliers import supplier_bp
from routes.alerts import alert_bp
from routes.requests import request_bp
from routes.prediction import prediction_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(auth_bp, url_prefix="/api")
app.register_blueprint(admin_bp, url_prefix="/api/admin")
app.register_blueprint(user_bp, url_prefix="/api/user")
app.register_blueprint(inventory_bp, url_prefix="/api/inventory")
app.register_blueprint(transaction_bp, url_prefix="/api/transactions")
app.register_blueprint(supplier_bp, url_prefix="/api/suppliers")
app.register_blueprint(alert_bp, url_prefix="/api/alerts")
app.register_blueprint(request_bp, url_prefix="/api/requests")
app.register_blueprint(prediction_bp, url_prefix="/api/prediction")


@app.route("/")
def home():
    return {
        "message": "Continuous Monitoring Smart Inventory System API",
        "status": "running"
    }


if __name__ == "__main__":
    app.run(debug=True, port=5000)