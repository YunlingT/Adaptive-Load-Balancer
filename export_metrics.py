# export_metrics.py
import requests
import pandas as pd
import time
from datetime import datetime

PROM_URL = "http://localhost:9090"
EXPORT_FILE = "load_timeseries.csv"
INTERVAL = 15  # seconds

def query_prometheus():
    query = 'sum(rate(http_requests_total[1m])) by (service)'
    r = requests.get(f"{PROM_URL}/api/v1/query", params={"query": query})
    results = r.json()["data"]["result"]
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return [
        {"timestamp": ts, "service": res["metric"]["service"], "request_rate": float(res["value"][1])}
        for res in results
    ]

while True:
    try:
        data = query_prometheus()
        df = pd.DataFrame(data)
        df.to_csv(EXPORT_FILE, mode="a", index=False, header=not pd.io.common.file_exists(EXPORT_FILE))
        print(f"[{datetime.now().strftime('%T')}] Exported {len(df)} rows")
    except Exception as e:
        print("Failed to fetch or write metrics:", e)
    time.sleep(INTERVAL)
