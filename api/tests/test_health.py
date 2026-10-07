from fastapi.testclient import TestClient

from app.main import app


def test_health_reports_ok_with_real_database():
    with TestClient(app) as client:
        res = client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["db"] == "ok"
    assert body["version"]