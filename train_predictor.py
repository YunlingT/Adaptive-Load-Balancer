# train_predictor.py
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib

df = pd.read_csv("load_timeseries.csv")
df_grouped = df.groupby("timestamp").sum().reset_index()

# Make lag features
for i in range(1, 6):
    df_grouped[f"lag_{i}"] = df_grouped["request_rate"].shift(i)

df_grouped.dropna(inplace=True)

X = df_grouped[[f"lag_{i}" for i in range(1, 6)]]
y = df_grouped["request_rate"]

model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

joblib.dump(model, "traffic_predictor.pkl")
print("✅ Model trained and saved as traffic_predictor.pkl")
