from fastapi.testclient import TestClient

from app.core.config import settings


def test_trading_ws_flow(client: TestClient, superuser_token_headers: dict[str, str]):
    """
    Test the full trading flow:
    1. Connect to WebSocket
    2. Place Order (REST)
    3. Receive WS updates (Submitted, Filled)
    4. Verify REST state
    """
    # Extract token
    token = superuser_token_headers["Authorization"].split(" ")[1]

    # Establish WebSocket connection
    with client.websocket_connect(f"/ws/trading/live?token={token}") as websocket:

        # Place Order via REST API
        order_payload = {
            "coin_type": "BTC",
            "side": "buy",
            "order_type": "market",
            "quantity": 1000.0 # AUD
        }

        response = client.post(
            f"{settings.API_V1_STR}/floor/trading/orders",
            headers=superuser_token_headers,
            json=order_payload,
        )
        assert response.status_code == 200
        order_data = response.json()
        order_id = order_data["id"]
        assert order_data["status"] == "pending"

        # Expect 'order_update' (submitted)
        msg1 = websocket.receive_json()
        assert msg1["type"] == "order_update"
        assert "id" in msg1["data"]
        assert msg1["data"]["id"] == order_id
        assert msg1["data"]["status"] == "submitted"

        # Expect 'order_update' (filled)
        msg2 = websocket.receive_json()
        assert msg2["type"] == "order_update"
        assert "id" in msg2["data"], f"ID missing in msg2 data: {msg2['data']}"
        assert msg2["data"]["id"] == order_id
        assert msg2["data"]["status"] == "filled"

        # Expect 'position_update'
        msg3 = websocket.receive_json()
        assert msg3["type"] == "position_update"
        assert "coin_type" in msg3["data"]
        assert msg3["data"]["coin_type"] == "BTC"

        # Verify REST state
        response = client.get(f"{settings.API_V1_STR}/floor/trading/orders", headers=superuser_token_headers)
        orders = response.json()
        assert any(o["id"] == order_id and o["status"] == "filled" for o in orders)

        response = client.get(f"{settings.API_V1_STR}/floor/trading/positions", headers=superuser_token_headers)
        positions = response.json()
        assert any(p["coin_type"] == "BTC" for p in positions)
