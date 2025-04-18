from locust import HttpUser, TaskSet, task, between
import random
import os

class UserBehavior(TaskSet):
    
    def on_start(self):
        print("🟡 Verifying load balancer is reachable from Locust client...")
        try:
            r = self.client.get("/", timeout=3)
            print(f"🟢 Success: load balancer returned {r.status_code}")
        except Exception as e:
            print("🔴 Error: could not reach load balancer ->", e)
            
    # @task
    # def fixed_strategy(self):
    #     self.client.get("/?strategy=round_robin")


    @task(1)
    def use_random_strategy(self):
        strategy = random.choice([
            "round_robin",
            "weighted_round_robin",
            "least_connections",
            "weighted_least_connections",
            "least_response_time"
        ])
        try:
            self.client.get(f"/?strategy={strategy}", timeout=5)
        except Exception as e:
            print("Request failed:", e)
        
class LoadBalancerUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def use_given_strategy(self):
        strategy = os.getenv("STRATEGY", "round_robin")
        print(f"🧪 Using strategy: {strategy}")
        self.client.get(f"/?strategy={strategy}")