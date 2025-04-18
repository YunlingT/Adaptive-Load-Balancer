from flask import Flask, request, Response
import requests
import hashlib
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
import requests as pyreq
import random
from predictor import LoadPredictor

app = Flask(__name__)

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP Requests", ["strategy", "service"])
RESPONSE_TIME = Histogram("response_time_seconds", "Response time in seconds", ["strategy", "service"])
FAILED_REQUESTS = Counter("http_requests_failed", "Failed HTTP Requests", ["strategy", "service"])

predictor = LoadPredictor()


PROMETHEUS_URL = "http://prometheus:9090"

# Backend service pool
services = [
    {"url": "http://service_1:5000", "weight": 3},
    {"url": "http://service_2:5000", "weight": 2},
    {"url": "http://service_3:5000", "weight": 1},
]

rr_counter = 0
wrr_counter = 0
wrr_list = []

# counter = 0

def init_weighted_list():
    global wrr_list
    wrr_list = []
    for service in services:
        wrr_list.extend([service["url"]] * service["weight"])

init_weighted_list()

# Add runtime state tracking
live_connections = {
    "http://service_1:5000": 0,
    "http://service_2:5000": 0,
    "http://service_3:5000": 0,
}

# Recent response times (updated after each request)
recent_response_time = {
    "http://service_1:5000": 1.0,
    "http://service_2:5000": 1.0,
    "http://service_3:5000": 1.0,
}

# Simulated weights for services
service_weights = {
    "http://service_1:5000": 3,
    "http://service_2:5000": 2,
    "http://service_3:5000": 1,
}

@app.route("/")
def balance():
    strategy = request.args.get("strategy", "round_robin")
    
    # === ML-BASED LOAD PREDICTION LOGIC ===
    predictor.add_observation(100)  # Optionally: replace 100 with actual recent load
    predicted = predictor.predict_next()
    if predicted and predicted > 120:
        print(f"⚠️ Predicted overload: {predicted:.2f}")
        strategy = "least_response_time"
        
    # === Strategy Routing ===
    if strategy == "ip_hash":
        client_ip = request.remote_addr
        target = ip_hash(client_ip)
    elif strategy == "weighted_round_robin":
        target = weighted_round_robin()
    elif strategy == "least_connections":
        target = least_connections()
    elif strategy == "weighted_least_connections":
        target = weighted_least_connections()
    elif strategy == "least_response_time":
        target = least_response_time()
    elif strategy == "resource":
        target = resource_based()
    else:
        target = round_robin()

    #track connections + response time
    live_connections[target] += 1
    
    start = time.time()
    
    try:
        resp = requests.get(target)
        duration = time.time() - start
        recent_response_time[target] = duration
        
        # Prometheus metrics
        REQUEST_COUNT.labels(strategy=strategy, service=target).inc()
        RESPONSE_TIME.labels(strategy=strategy, service=target).observe(duration)
        # Count failures explicitly
        if resp.status_code >= 500:
            FAILED_REQUESTS.labels(strategy=strategy, service=target).inc()

        return resp.text
    except Exception as e:
        FAILED_REQUESTS.labels(strategy=strategy, service=target).inc()
        return f"Request failed: {e}", 500
    #     return f"[{strategy.upper()}] -> {target}\n" + resp.text
    
    # except Exception as e:
    #     return f"Error forwarding to {target}: {e}", 500
    
    finally:
        live_connections[target] -= 1    

    
@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


# ----- Algorithms -----

def round_robin():
    global rr_counter
    target = services[rr_counter % len(services)]["url"]
    rr_counter += 1
    return target

def weighted_round_robin():
    global wrr_counter
    if not wrr_list:
        init_weighted_list()
    target = wrr_list[wrr_counter % len(wrr_list)]
    print(f"WRR Counter: {wrr_counter}, Target: {target}")
    wrr_counter += 1
    return target

def ip_hash(ip):
    ip_hash_val = int(hashlib.md5(ip.encode()).hexdigest(), 16)
    idx = ip_hash_val % len(services)
    return services[idx]["url"]

def least_connections():
    return min(live_connections, key=live_connections.get)

def weighted_least_connections():
    score = {
        svc : live_connections[svc] / service_weights[svc]
        for svc in live_connections 
    }
    return min(score, key=score.get)

def least_response_time():
    return min(recent_response_time, key=recent_response_time.get)

def get_cpu_usage(service_label):
    query = f'rate(container_cpu_usage_seconds_total{{name="{service_label}"}}[1m])'
    r = pyreq.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query})
    try:
        results = r.json()["data"]["result"]
        return float(results[0]["value"][1]) if results else float("inf")
    except:
        return float("inf")
    
def resource_based():
    usages = {
        svc: get_cpu_usage(svc.split("//")[1].split(":")[0])  # service_1 from http://service_1:5000
        for svc in live_connections
    }
    return min(usages, key=usages.get)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
    
