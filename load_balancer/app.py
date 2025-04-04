from flask import Flask, request
import requests
import hashlib
from prometheus_client import Counter, Histogram, generate_latest
import time

app = Flask(__name__)

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP Requests", ["strategy", "service"])
RESPONSE_TIME = Histogram("response_time_seconds", "Response time in seconds", ["strategy", "service"])

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


@app.route("/")
def balance():
    strategy = request.args.get("strategy", "round_robin")
    
    if strategy == "ip_hash":
        client_ip = request.remmote_addr
        target = ip_hash(client_ip)
    elif strategy == "weighted_round_robin":
        target = weighted_round_robin()
    else:
        target = round_robin()
        
    # try:
    #     resp = requests.get(target)
    #     return f"{strategy.upper()}] -> {target}\n" + resp.text
    # except Exception as e:
    #     return f"Error forwarding to {target}: {e}", 500

    try:
        start_time = time.time()
        resp = requests.get(target)
        duration = time.time() - start_time

        REQUEST_COUNT.labels(strategy=strategy, service=target).inc()
        RESPONSE_TIME.labels(strategy=strategy, service=target).observe(duration)

        return f"[{strategy.upper()}] -> {target}\n" + resp.text
    except Exception as e:
        return f"Error forwarding to {target}: {e}", 500
    
@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": "text/plain"}


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

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
    
