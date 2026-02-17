import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.main import app
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email


def test_websocket_catalyst_connection(session: Session):
    client = TestClient(app)
    email = random_email()
    headers = authentication_token_from_email(client=client, email=email, db=session)
    token = headers["Authorization"].split(" ")[1]

    with client.websocket_connect(f"/ws/catalyst/live?token={token}"):
        # Connection established
        pass

def test_websocket_glass_connection(session: Session):
    client = TestClient(app)
    email = random_email()
    headers = authentication_token_from_email(client=client, email=email, db=session)
    token = headers["Authorization"].split(" ")[1]

    with client.websocket_connect(f"/ws/glass/live?token={token}"):
        pass

def test_websocket_human_connection(session: Session):
    client = TestClient(app)
    email = random_email()
    headers = authentication_token_from_email(client=client, email=email, db=session)
    token = headers["Authorization"].split(" ")[1]

    with client.websocket_connect(f"/ws/human/live?token={token}"):
        pass

def test_websocket_exchange_connection(session: Session):
    client = TestClient(app)
    email = random_email()
    headers = authentication_token_from_email(client=client, email=email, db=session)
    token = headers["Authorization"].split(" ")[1]

    with client.websocket_connect(f"/ws/exchange/live?token={token}"):
        pass

def test_websocket_invalid_token():
    client = TestClient(app)
    with pytest.raises(Exception):  # noqa: B017
        with client.websocket_connect("/ws/catalyst/live?token=invalid"):
            pass
