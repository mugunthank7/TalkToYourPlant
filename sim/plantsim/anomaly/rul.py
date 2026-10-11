class ShiftedModel:
    """A regression model plus a constant offset (used for split-conformal prediction intervals in log space)."""

    def __init__(self, model, offset: float) -> None:
        self.model, self.offset = model, offset

    def predict(self, X):
        return self.model.predict(X) + self.offset
