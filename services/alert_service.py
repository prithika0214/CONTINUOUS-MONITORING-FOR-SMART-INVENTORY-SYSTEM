def check_alert(quantity, minimum_stock):

    if quantity == 0:
        return "Out of Stock"

    if quantity <= minimum_stock:
        return "Low Stock"

    return "Healthy"