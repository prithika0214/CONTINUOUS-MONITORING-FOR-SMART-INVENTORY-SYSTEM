class Transaction:

    def __init__(
        self,
        id,
        product_id,
        user_id,
        transaction_type,
        quantity,
        created_at
    ):
        self.id = id
        self.product_id = product_id
        self.user_id = user_id
        self.transaction_type = transaction_type
        self.quantity = quantity
        self.created_at = created_at