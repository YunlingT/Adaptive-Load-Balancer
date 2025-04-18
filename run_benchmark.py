import subprocess
import time
import os

strategies = [
    "round_robin",
    "weighted_round_robin",
    "least_connections",
    "weighted_least_connections",
    "least_response_time"
]

def run_strategy(strategy):
    print(f"Starting test for strategy: {strategy}")
    env = os.environ.copy()
    env["STRATEGY"] = strategy

    # Run Locust
    subprocess.run([
        "locust", "-f", "locustfile.py",
        "--headless", "--host", "http://localhost:8080",
        "-u", "50", "-r", "10", "--run-time", "45s",
        "--stop-timeout", "5", "--loglevel", "WARNING", "--only-summary"
    ], env=env)

    print("Waiting 15s for Prometheus to scrape...")
    time.sleep(15)

    print("Collecting metrics for strategy...")
    subprocess.run(["python", "collect_metrics.py"], env=env)

def main():
    for strategy in strategies:
        run_strategy(strategy)

if __name__ == "__main__":
    main()
