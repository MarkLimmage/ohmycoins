import os
import random
import time

import httpx

# Running inside container
BASE_URL = "http://localhost:8000/api/v1"

USERNAME = os.getenv("FIRST_SUPERUSER", "admin@example.com")
PASSWORD = os.getenv("FIRST_SUPERUSER_PASSWORD", "changethis")

def main():

    # Authenticate
    try:
        r = httpx.post(f"{BASE_URL}/login/access-token", data={
            "username": USERNAME,
            "password": PASSWORD
        })
        if r.status_code != 200:
             # Fallback
             r = httpx.post(f"{BASE_URL}/login/access-token", data={
                "username": USERNAME,
                "password": "adminadmin"
            })

        if r.status_code != 200:
            return

        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

    except Exception:
        return

    assets = ["BTC", "ETH", "SOL", "XRP", "ADA"]
    decisions = ["BUY", "SELL", "HOLD"]
    agents = ["strategy_momentum_v1", "strategy_mean_reversion_v2", "guard_rail_max_drawdown"]

    for _i in range(15):
        decision = random.choice(decisions)
        asset = random.choice(assets)
        agent_id = random.choice(agents)
        confidence = random.uniform(0.5, 0.99)
        price = random.uniform(10.0, 50000.0)

        is_executed = decision != "HOLD"
        block_reason = None

        # Simulate Guard blocking
        if decision != "HOLD" and random.random() < 0.2:
            is_executed = False
            block_reason = "Risk Limit Exceeded: Daily Loss > 5%"

        data = {
            "agent_id": agent_id,
            "asset": asset,
            "decision": decision,
            "reason": f"Market conditions favorable for {decision} {asset} due to RSI divergence.",
            "confidence_score": confidence,
            "price_at_decision": price,
            "is_executed": is_executed,
            "block_reason": block_reason
        }

        r = httpx.post(
            f"{BASE_URL}/audit/",
            json=data,
            headers=headers
        )

        if r.status_code == 200:
            pass
        else:
            pass

        time.sleep(0.1)

if __name__ == "__main__":
    main()
