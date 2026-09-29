class Inventory:

    def __init__(
        self,
        id,
        product_name,
        category,
        quantity,
        minimum_stock,
        price,
        barcode,
        supplier_id
    ):
        self.id = id
        self.product_name = product_name
        self.category = category
        self.quantity = quantity
        self.minimum_stock = minimum_stock
        self.price = price
        self.barcode = barcode
        self.supplier_id = supplier_id

    def status(self):

        if self.quantity == 0:
            return "Out of Stock"

        elif self.quantity <= self.minimum_stock:
            return "Low Stock"

        return "Healthy"