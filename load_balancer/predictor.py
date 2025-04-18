# predictor.py
import joblib
from collections import deque

class LoadPredictor:
    def __init__(self, model_path="traffic_predictor.pkl"):
        self.model = joblib.load(model_path)
        self.recent_rates = deque(maxlen=5)

    def add_observation(self, rate):
        self.recent_rates.append(rate)

    def predict_next(self):
        if len(self.recent_rates) < 5:
            return None
        X = [list(self.recent_rates)]
        return self.model.predict(X)[0]
