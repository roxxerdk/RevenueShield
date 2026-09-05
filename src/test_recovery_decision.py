from recovery_decision import (
    RecoveryDecisionService
)


print("===== REVENUESHIELD DECISION TEST =====")


service = RecoveryDecisionService()


transaction = {
    "transaction_id": "TEST_TXN_001",

    "amount": 5000.0,

    "attempt_number": 1,
    "checkout_duration_sec": 120.0,
    "hour_of_day": 14,
    "day_of_week": 2,

    "account_age_days": 300,
    "total_transactions": 20,
    "successful_transactions": 15,
    "failed_transactions": 5,

    "historical_success_rate": 0.75,

    "average_transaction_value": 4500.0,
    "median_transaction_value": 4200.0,
    "total_spend": 90000.0,

    "days_since_last_success": 3,

    "previous_recovery_attempts": 0,
    "previous_recoveries": 0,

    "currency": "INR",
    "payment_method": "upi",
    "status": "failed",

    "failure_reason": "network_error",
    "failure_source": "network",
    "failure_step": "authorization",

    "subscription_status": None,

    "device_type": "mobile",
    "customer_segment": "regular",

    "checkout_started": True,
    "is_subscription": False,
    "is_new_device": False,
}


result = service.decide(
    transaction
)


print("\n===== RECOVERY PROBABILITIES =====")

for action, probability in (
    result["probabilities"].items()
):

    print(
        f"{action:<12}: "
        f"{probability:.4f}"
    )


print("\n===== DECISION =====")

print(
    "Selected action:",
    result["selected_action"]
)

print(
    "Allowed:",
    result["allowed"]
)

print(
    "Expected value:",
    f"₹{result['expected_value']:,.2f}"
)

print(
    "Risk level:",
    result["risk_level"]
)

print(
    "Reason:",
    result["reason"]
)

print(
    "\n===== REVENUESHIELD DECISION TEST COMPLETE ====="
)