import requests
import pandas as pd
from tabulate import tabulate
from datetime import datetime
import os

PROM_URL = "http://localhost:9090"
LOG_FILE = "scraped_metrics_log.txt"

strategies = [
    "round_robin",
    "weighted_round_robin",
    "least_connections",
    "weighted_least_connections",
    "least_response_time"
]

def query_prometheus(promql):
    response = requests.get(f"{PROM_URL}/api/v1/query", params={"query": promql})
    if response.status_code != 200:
        print("Prometheus query failed:", promql)
        return []
    return response.json()["data"]["result"]

def parse_single_value(result):
    if result and "value" in result[0]:
        return float(result[0]["value"][1])
    return 0.0

def get_service_throughput(strategy):
    query = f'rate(http_requests_total{{strategy="{strategy}"}}[2m])'
    results = query_prometheus(query)
    per_service = {}
    for r in results:
        svc = r["metric"].get("service", "unknown")
        val = float(r["value"][1])
        per_service[svc] = round(val, 2)
    return per_service

def log_scraped(strategy, avg_latency, throughput, failure_rate, per_service_throughput):
    with open(LOG_FILE, "a") as f:
        f.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Strategy: {strategy}\n")
        f.write(f"  Avg Latency (ms): {avg_latency}\n")
        f.write(f"  Throughput (req/s): {throughput}\n")
        f.write(f"  Failure Rate (%): {failure_rate}\n")
        f.write("  Per-Service Throughput:\n")
        for svc, val in per_service_throughput.items():
            f.write(f"    - {svc}: {val} rps\n")

def get_metrics_for_strategy(strategy):
    avg_latency_query = f'rate(response_time_seconds_sum{{strategy="{strategy}"}}[2m]) / rate(response_time_seconds_count{{strategy="{strategy}"}}[2m])'
    throughput_query = f'sum(rate(http_requests_total{{strategy="{strategy}"}}[2m]))'
    failed_query = f'sum(rate(http_requests_failed{{strategy="{strategy}"}}[2m]))'

    avg_latency = parse_single_value(query_prometheus(avg_latency_query)) * 1000  # to ms
    throughput = parse_single_value(query_prometheus(throughput_query))

    total = throughput
    failed = parse_single_value(query_prometheus(failed_query)) if query_prometheus(failed_query) else 0.0
    failure_rate = (failed / total) * 100 if total > 0 else 0.0

    per_service = get_service_throughput(strategy)

    # Log to file
    log_scraped(strategy, avg_latency, throughput, failure_rate, per_service)

    return {
        "Strategy": strategy,
        "Avg Latency (ms)": round(avg_latency, 2),
        "Throughput (req/s)": round(throughput, 2),
        "Failure Rate (%)": round(failure_rate, 2),
        "Per-Service Throughput": ", ".join(f"{k.split('//')[1]}: {v} rps" for k, v in per_service.items())
    }

def main():
    strategy = os.getenv("STRATEGY")
    if not strategy:
        print("STRATEGY environment variable is not set.")
        return

    print(f"Collecting metrics for strategy: {strategy}")
    metrics = get_metrics_for_strategy(strategy)

    # Add timestamp
    metrics["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Append to CSV
    df = pd.DataFrame([metrics])
    csv_path = "incremental_performance_metrics.csv"
    df.to_csv(csv_path, mode="a", index=False, header=not pd.io.common.file_exists(csv_path))

    print(tabulate(df, headers="keys", tablefmt="pretty"))
    print(f"Appended to {csv_path}")

if __name__ == "__main__":
    main()
