from flask import Flask
import time
import random

app = Flask(__name__)

@app.route("/")
def home():
    delay = random.uniform(0.1, 1.0)  # simulate random processing delay
    time.sleep(delay)
    return f"Hello from Service 1! Delay: {delay:.2f}s\n"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)