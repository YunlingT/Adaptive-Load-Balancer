import subprocess
import os
import time
import pandas as pd
from datetime import datetime
from collect_metrics import get_metrics_for_strategy

# CSV_FILE = "incremental_performance_metrics.csv"
CSV_FILE = "incremental_metrics.csv"

strategies = [
    "round_robin",
    "weighted_round_robin",
    "least_connections",
    "weighted_least_connections",
    "least_response_time"
]

def already_logged(strategy):
    if not os.path.exists(CSV_FILE):
        return False
    df = pd.read_csv(CSV_FILE)
    return strategy in df["Strategy"].values

def run_locust(strategy):
    print(f"Running Locust for strategy: {strategy}")
    env = os.environ.copy()
    env["STRATEGY"] = strategy

    subprocess.run([
        "locust", "-f", "locustfile.py",
        "--headless", "--host", "http://localhost:8080",
        "-u", "50", "-r", "10", "--run-time", "45s",
        "--stop-timeout", "5", "--loglevel", "WARNING", "--only-summary"
    ], env=env)

def scrape_and_log(strategy):
    print(f"Scraping Prometheus for: {strategy}")
    metrics = get_metrics_for_strategy(strategy)
    metrics["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    df = pd.DataFrame([metrics])
    df.to_csv(CSV_FILE, mode='a', index=False, header=not os.path.exists(CSV_FILE))
    print(f"Appended: {strategy}")

def main():
    for strategy in strategies:
        if already_logged(strategy):
            print(f"Already logged: {strategy}")
            continue

        run_locust(strategy)
        print("Waiting 15s for Prometheus scrape...")
        time.sleep(15)
        scrape_and_log(strategy)

if __name__ == "__main__":
    main()
