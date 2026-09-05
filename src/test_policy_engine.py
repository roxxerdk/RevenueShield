from policy_engine import RecoveryPolicy


policy = RecoveryPolicy()


print("===== POLICY ENGINE TEST =====")


# --------------------------------------------------
# Test 1: Normal transaction
# --------------------------------------------------

decision = policy.evaluate(
    amount=5000,
    probabilities={
        "retry": 0.70,
        "reminder": 0.50,
        "escalation": 0.40,
    },
)

print("\nTest 1")
print(decision)


# --------------------------------------------------
# Test 2: Very low recovery probability
# --------------------------------------------------

decision = policy.evaluate(
    amount=500,
    probabilities={
        "retry": 0.01,
        "reminder": 0.01,
        "escalation": 0.01,
    },
)

print("\nTest 2")
print(decision)


# --------------------------------------------------
# Test 3: Invalid probability
# --------------------------------------------------

decision = policy.evaluate(
    amount=5000,
    probabilities={
        "retry": 1.2,
        "reminder": 0.5,
        "escalation": 0.4,
    },
)

print("\nTest 3")
print(decision)


# --------------------------------------------------
# Test 4: Extremely high transaction
# --------------------------------------------------

decision = policy.evaluate(
    amount=600000,
    probabilities={
        "retry": 0.90,
        "reminder": 0.80,
        "escalation": 0.95,
    },
)

print("\nTest 4")
print(decision)


print("\n===== POLICY ENGINE TEST COMPLETE =====")