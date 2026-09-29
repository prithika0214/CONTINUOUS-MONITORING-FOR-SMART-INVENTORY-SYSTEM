class StockRequest:

    def __init__(
        self,
        id,
        user_id,
        product_id,
        quantity,
        reason,
        status,
        created_at
    ):
        self.id = id
        self.user_id = user_id
        self.product_id = product_id
        self.quantity = quantity
        self.reason = reason
        self.status = status
        self.created_at = created_at