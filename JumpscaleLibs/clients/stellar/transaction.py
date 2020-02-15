class TransactionSummary(object):
    def __init__(self, hash, memo_text=None, created_at=None):
        self.hash = hash
        self.memo_text = memo_text
        self.created_at = created_at

    @staticmethod
    def from_horizon_response(response_transaction):
        hash = response_transaction["hash"]
        created_at = response_transaction["created_at"]
        memo_text = None
        if "memo" in response_transaction:
            if response_transaction["memo_type"] == "text":
                memo_text = response_transaction["memo"]
        return TransactionSummary(hash, memo_text, created_at)

    def __str__(self):
        representation = "{hash} created at {created_at}".format(hash=self.hash, created_at=self.created_at)
        if self.memo_text is not None:
            representation += " with memo text '{memo_text}'".format(memo_text=self.memo_text)
        return representation

    def __repr__(self):
        return str(self)
