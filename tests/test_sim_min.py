from fastapi.testclient import TestClient
from main import app

c = TestClient(app)

def test_sim_health():
    r = c.get("/sim/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_sim_echo_ok():
    r = c.post("/sim/echo", json={"outdir":"run1","msg":"hi"})
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True and j["outdir"] == "run1" and j["msg"] == "hi"

def test_sim_echo_bad_outdir():
    r = c.post("/sim/echo", json={"outdir":"..","msg":"x"})
    assert r.status_code == 400
