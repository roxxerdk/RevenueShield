"""Tests for FastAPI endpoints."""
import uuid
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "RevenueShield"

def test_config_endpoint():
    res = client.get("/api/config")
    assert res.status_code == 200
    data = res.json()
    assert "policy" in data
    assert "action_costs" in data["policy"]

def test_metrics_endpoint():
    res = client.get("/api/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "revenue_at_risk" in data
    assert "recovered_revenue" in data
    assert "recovery_rate_pct" in data

def test_evaluate_and_execute_endpoint():
    txn_id = f"API_TEST_TXN_{uuid.uuid4().hex[:8]}"
    eval_payload = {
        "transaction_id": txn_id,
        "amount": 4000.0,
        "currency": "INR",
        "payment_method": "card",
        "status": "failed",
        "failure_reason": "network_error",
    }
    
    # 1. Evaluate
    res_eval = client.post("/api/recoveries/evaluate", json=eval_payload)
    assert res_eval.status_code == 200
    eval_data = res_eval.json()
    assert eval_data["transaction_id"] == txn_id
    assert "probabilities" in eval_data
    assert "selected_action" in eval_data

    # 2. Execute
    exec_payload = {"transaction_id": txn_id}
    res_exec = client.post("/api/recoveries/execute", json=exec_payload)
    assert res_exec.status_code == 200
    exec_data = res_exec.json()
    assert "execution" in exec_data
    assert exec_data["execution"]["executed"] is True

    # 3. Simulate payment
    sim_payload = {"amount": 4000.0, "status": "captured"}
    res_sim = client.post(f"/api/recoveries/{txn_id}/simulate-payment", json=sim_payload)
    assert res_sim.status_code == 200
    sim_res = res_sim.json()["result"]
    assert sim_res.get("recovered") is True

    # 4. Get detail
    res_detail = client.get(f"/api/recoveries/{txn_id}")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["case"]["recovered"] is True
    assert len(detail["decisions"]) > 0
    assert len(detail["actions"]) > 0
    assert len(detail["audit_logs"]) > 0
