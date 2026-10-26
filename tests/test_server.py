import pytest
from fastapi.testclient import TestClient

from meetai.server.app import create_app


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/t.db")
    with TestClient(create_app()) as c:
        yield c


def test_missing_database_url_fails_loudly(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        create_app()


def test_status_and_empty_sessions(client):
    assert client.get("/api/status").json() == {"running": False, "session_id": None}
    assert client.get("/api/sessions").json() == []


def test_websocket_sends_initial_status(client):
    with client.websocket_connect("/ws") as ws:
        assert ws.receive_json() == {"type": "status", "running": False}


def test_stop_without_session_is_noop(client):
    assert client.post("/api/sessions/stop").json() == {"running": False}


def test_disconnected_websocket_client_is_unsubscribed(client):
    import time

    hub = client.app.state.hub
    with client.websocket_connect("/ws") as ws:
        ws.receive_json()
        assert hub.client_count == 1
    for _ in range(50):  # the server notices the disconnect asynchronously
        if hub.client_count == 0:
            break
        time.sleep(0.05)
    assert hub.client_count == 0
