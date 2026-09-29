def get_status(quantity, minimum_stock):

    if quantity == 0:
        return "Out of Stock"

    if quantity <= minimum_stock:
        return "Low Stock"

    return "Healthy"


def calculate_inventory_value(quantity, price):

    return quantity * price