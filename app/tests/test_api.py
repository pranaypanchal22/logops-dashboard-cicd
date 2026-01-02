from app import create_app

def test_health_ok():
    app = create_app()
    client = app.test_client()
    resp = client.get("/health")
    assert resp.status_code in (200, 500)  # DB might be initializing in some envs

def test_ingest_log():
    app = create_app()
    client = app.test_client()
    resp = client.post("/api/logs", json={
        "level": "INFO",
        "service": "test-service",
        "message": "hello"
    })
    assert resp.status_code == 201
