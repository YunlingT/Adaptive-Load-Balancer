import subprocess
import time
import os

def run_export_metrics():
    print("🚀 Starting Prometheus exporter in background...")
    return subprocess.Popen(["python", "export_metrics.py"])

def run_locust_load():
    print("⚡ Generating load with Locust for 3 minutes...")
    subprocess.run([
        "locust", "-f", "locustfile.py",
        "--headless", "--host=http://localhost:8080",
        "-u", "100", "-r", "20", "--run-time", "180s",
        "--stop-timeout", "5", "--loglevel", "WARNING", "--only-summary"
    ])

def train_model():
    print("🧠 Training load prediction model...")
    subprocess.run(["python", "train_predictor.py"])

def restart_load_balancer():
    print("🔁 Restarting load balancer container...")
    subprocess.run(["docker-compose", "restart", "load_balancer"])
    print("✅ Load balancer restarted with prediction logic in place.")

def main():
    metrics_proc = run_export_metrics()
    time.sleep(5)  # give Prometheus a moment to warm up

    try:
        run_locust_load()
    finally:
        print("🛑 Stopping metrics exporter.")
        metrics_proc.terminate()

    train_model()
    # apply_prediction_patch()
    restart_load_balancer()

if __name__ == "__main__":
    main()
