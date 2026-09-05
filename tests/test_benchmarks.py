"""Performance & latency benchmarks for RevenueShield policy and prediction engine."""
import time
import pytest
from policy_engine import RecoveryPolicy
from recovery_predictor import RecoveryPredictor
from recovery_decision import RecoveryDecisionService

def test_policy_engine_evaluation_latency():
    policy = RecoveryPolicy()
    probs = {"retry": 0.65, "reminder": 0.45, "escalation": 0.55}
    
    start_time = time.perf_counter()
    for _ in range(1000):
        policy.evaluate(amount=5000.0, probabilities=probs)
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    
    avg_latency_ms = elapsed_ms / 1000
    # Policy evaluation must be sub-millisecond (< 0.1ms per transaction)
    assert avg_latency_ms < 0.1, f"Policy latency too high: {avg_latency_ms:.4f}ms"

def test_decision_service_throughput():
    service = RecoveryDecisionService()
    txn = {
        "transaction_id": "BENCH_TXN_001",
        "amount": 2500.0,
        "payment_method": "card",
        "status": "failed",
        "failure_reason": "network_error",
    }
    
    start_time = time.perf_counter()
    iterations = 50
    for _ in range(iterations):
        service.decide(txn)
    elapsed_sec = time.perf_counter() - start_time
    
    throughput_rps = iterations / elapsed_sec
    assert throughput_rps > 10, f"Throughput too low: {throughput_rps:.2f} rps"
