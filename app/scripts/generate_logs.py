import random
import time
import requests
from datetime import datetime, timezone

URL = "http://localhost:8080/api/logs"
SERVICES = ["auth-api", "payments", "orders", "frontend", "worker"]
LEVELS = ["INFO", "WARN", "ERROR"]

MESSAGES = {
    "INFO": ["User logged in", "Cache hit", "Job completed", "Request served"],
    "WARN": ["Slow response detected", "Retrying request", "Rate limit nearing"],
    "ERROR": ["Database timeout", "Null pointer exception", "Payment failed", "Upstream 502"]
}

def main(n=50, delay=0.05):
    for _ in range(n):
        level = random.choices(LEVELS, weights=[70, 20, 10])[0]
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": level,
            "service": random.choice(SERVICES),
            "message": random.choice(MESSAGES[level]),
            "metadata": {"request_id": random.randint(1000, 9999)}
        }
        r = requests.post(URL, json=payload, timeout=5)
        r.raise_for_status()
        time.sleep(delay)

    print(f"Sent {n} logs to {URL}")

if __name__ == "__main__":
    main()
