"""RevenueShield — AI-Assisted Revenue Recovery Dashboard.

Interactive control center for Razorpay AI Buildathon 2026.
Dynamically loads live data from the SQLite persistence layer and demonstrates
the complete lifecycle: Risk -> Diagnosis -> Prediction -> Policy Gate -> Execution -> Verification -> Audit.
"""
import sys
import os
from pathlib import Path
import json
import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func

# Add src to python path
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import settings
from database import get_db_session, init_db
from models.db_models import (
    RecoveryCase,
    RecoveryDecisionRecord,
    RecoveryActionRecord,
    AuditLogRecord,
    RecoveryState,
)
from recovery_workflow import recovery_workflow
from audit_logger import audit_logger

# Page configuration
st.set_page_config(
    page_title="RevenueShield | AI Revenue Recovery",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize DB if needed
init_db()

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0F847B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #555;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .badge-test {
        background-color: #0284c7;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-sim {
        background-color: #64748b;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# Sidebar
# -------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=64)
    st.markdown("## **RevenueShield**")
    st.markdown("Track 03: *AI Revenue Recovery*")
    st.markdown("---")
    
    mode_label = "TEST MODE" if settings.is_test_mode else "DEMO SIMULATION"
    badge_class = "badge-test" if settings.is_test_mode else "badge-sim"
    st.markdown(f"**Runtime Mode**: <span class='{badge_class}'>{mode_label}</span>", unsafe_allow_html=True)
    st.markdown(f"**Razorpay Test Auth**: `{'Configured' if settings.has_razorpay_credentials else 'Simulation Fallback'}`")
    st.markdown(f"**Database**: SQLite (`{Path(settings.database_url.replace('sqlite:///', '')).name}`)")
    st.markdown("---")
    
    st.markdown("### ⚙️ **Configured Policy Rules**")
    st.markdown(f"- **Max Recovery Amount**: ₹{settings.policy_max_transaction_amount:,.0f}")
    st.markdown(f"- **Max Escalation Cap**: ₹{settings.policy_max_escalation_amount:,.0f}")
    st.markdown(f"- **Min Net Expected Value**: ₹{settings.policy_min_expected_value:,.2f}")
    st.markdown("### 💰 **Intervention Costs**")
    for act, cost in settings.action_costs.items():
        st.markdown(f"- `{act}`: ₹{cost:.2f}")

    st.markdown("---")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

# -------------------------------------------------------------
# Header
# -------------------------------------------------------------
st.markdown("<div class='main-header'>🛡️ RevenueShield: AI Revenue Recovery Engine</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Predictive revenue risk diagnosis, ML-guided economic optimization, and deterministic safety policy governance for Razorpay payments.</div>", unsafe_allow_html=True)

# Fetch Metrics from Database
with get_db_session() as session:
    total_cases = session.query(RecoveryCase).count()
    revenue_at_risk = session.query(func.sum(RecoveryCase.amount)).scalar() or 0.0
    recovered_revenue = session.query(func.sum(RecoveryCase.amount_recovered)).scalar() or 0.0
    net_recovered = session.query(func.sum(RecoveryCase.net_recovered)).scalar() or 0.0
    recovered_count = session.query(RecoveryCase).filter(RecoveryCase.recovered == True).count()
    pending_count = session.query(RecoveryCase).filter(
        RecoveryCase.status.in_([RecoveryState.PAYMENT_PENDING.value, RecoveryState.ACTION_EXECUTED.value, RecoveryState.AT_RISK.value])
    ).count()
    blocked_count = session.query(RecoveryCase).filter(
        RecoveryCase.status == RecoveryState.POLICY_BLOCKED.value
    ).count()

recovery_rate = (recovered_count / total_cases * 100.0) if total_cases > 0 else 0.0

# Top KPI Metric Cards
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Revenue at Risk", f"₹{revenue_at_risk:,.2f}")
col2.metric("Recovered Revenue", f"₹{recovered_revenue:,.2f}")
col3.metric("Net Economic Gain", f"₹{net_recovered:,.2f}")
col4.metric("Recovery Rate", f"{recovery_rate:.1f}%")
col5.metric("Pending Recoveries", f"{pending_count}")
col6.metric("Policy Blocked", f"{blocked_count}")

st.markdown("---")

# -------------------------------------------------------------
# Main Navigation Tabs
# -------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Pipeline & Overview",
    "🔍 Recovery Cases Explorer",
    "⚡ Live Interactive Sandbox",
    "📜 Machine-Readable Audit Logs",
])

# TAB 1: Pipeline & Overview
with tab1:
    st.subheader("System Architecture & Governance Pipeline")
    st.markdown("""
    ```
    Failed Transaction  ──> [ Failure Diagnosis ]
                                    │
                                    ▼
                        [ ML Recovery Prediction ]
                        P(Retry) | P(Reminder) | P(Escalation)
                                    │
                                    ▼
                        [ Expected Net Recovery ]
                        EV = P(Success) × Amount - Cost
                                    │
                                    ▼
                        [ Deterministic Policy Gate ]
                            /               \\
                      Approved             Blocked (High Risk / Unviable)
                         │                      │
                         ▼                      ▼
                  [ Execution ]            [ Audit Log ]
            (Razorpay Test Mode Order)
                         │
                         ▼
             [ Webhook Verification ]
            (HMAC SHA256 Signature)
                         │
                         ▼
               [ Recovered Revenue ]
    ```
    """)
    
    st.markdown("### Performance & Action Distribution")
    c1, c2 = st.columns(2)
    with c1:
        with get_db_session() as session:
            action_counts = {
                "Retry": session.query(RecoveryActionRecord).filter(RecoveryActionRecord.action_type == "retry").count(),
                "Reminder": session.query(RecoveryActionRecord).filter(RecoveryActionRecord.action_type == "reminder").count(),
                "Escalation": session.query(RecoveryActionRecord).filter(RecoveryActionRecord.action_type == "escalation").count(),
            }
        st.bar_chart(pd.DataFrame(list(action_counts.items()), columns=["Action", "Count"]).set_index("Action"))
        st.caption("Interventions executed across evaluated cases")

    with c2:
        with get_db_session() as session:
            risk_counts = {
                "Low Risk": session.query(RecoveryCase).filter(RecoveryCase.risk_level == "low").count(),
                "Medium Risk": session.query(RecoveryCase).filter(RecoveryCase.risk_level == "medium").count(),
                "High Risk": session.query(RecoveryCase).filter(RecoveryCase.risk_level == "high").count(),
            }
        st.bar_chart(pd.DataFrame(list(risk_counts.items()), columns=["Risk Level", "Count"]).set_index("Risk Level"))
        st.caption("Risk tier classification derived from deterministic expected recovery thresholds")

# TAB 2: Recovery Cases Explorer
with tab2:
    st.subheader("Persisted Recovery Cases Explorer")
    
    with get_db_session() as session:
        cases = session.query(RecoveryCase).order_by(RecoveryCase.updated_at.desc()).all()
        cases_data = [
            {
                "Transaction ID": c.transaction_id,
                "Customer ID": c.customer_id,
                "Amount (₹)": c.amount,
                "Status": c.status,
                "Failure Reason": c.failure_reason,
                "Risk Tier": c.risk_level,
                "Recovered": "✅ Yes" if c.recovered else "❌ No",
                "Recovered (₹)": c.amount_recovered,
                "Razorpay Order ID": c.razorpay_order_id or "-",
                "Last Updated": c.updated_at.strftime("%Y-%m-%d %H:%M:%S") if c.updated_at else "-",
            }
            for c in cases
        ]
        df_cases = pd.DataFrame(cases_data)

    if not df_cases.empty:
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            status_options = ["All"] + list(df_cases["Status"].unique())
            selected_status = st.selectbox("Filter by Status", status_options)
        with filter_col2:
            search_tx = st.text_input("Search Transaction ID")

        filtered_df = df_cases.copy()
        if selected_status != "All":
            filtered_df = filtered_df[filtered_df["Status"] == selected_status]
        if search_tx:
            filtered_df = filtered_df[filtered_df["Transaction ID"].str.contains(search_tx, case=False, na=False)]

        st.dataframe(filtered_df, use_container_width=True)

        st.markdown("### 🔎 **Transaction Detail Drilldown**")
        selected_tx_id = st.selectbox("Select Transaction to Inspect", options=df_cases["Transaction ID"].tolist())
        
        if selected_tx_id:
            with get_db_session() as session:
                selected_case = session.query(RecoveryCase).filter(RecoveryCase.transaction_id == selected_tx_id).first()
                if selected_case:
                    d_col1, d_col2 = st.columns(2)
                    with d_col1:
                        st.markdown(f"**Transaction ID**: `{selected_case.transaction_id}`")
                        st.markdown(f"**Customer ID**: `{selected_case.customer_id}`")
                        st.markdown(f"**Amount**: ₹{selected_case.amount:,.2f}")
                        st.markdown(f"**Status**: `{selected_case.status}`")
                        st.markdown(f"**Failure Reason**: `{selected_case.failure_reason}` ({selected_case.failure_source})")
                        st.markdown(f"**Razorpay Order ID**: `{selected_case.razorpay_order_id or 'N/A'}`")
                    
                    with d_col2:
                        if selected_case.decisions:
                            last_dec = selected_case.decisions[-1]
                            st.markdown(f"**ML Predictions**:")
                            st.markdown(f"- P(Retry): `{last_dec.p_retry:.4f}`")
                            st.markdown(f"- P(Reminder): `{last_dec.p_reminder:.4f}`")
                            st.markdown(f"- P(Escalation): `{last_dec.p_escalation:.4f}`")
                            st.markdown(f"**Selected Action**: `{last_dec.selected_action}`")
                            st.markdown(f"**Expected Value**: ₹{last_dec.expected_value:,.2f}")
                            st.markdown(f"**Policy Gate Decision**: `{'APPROVED' if last_dec.allowed else 'BLOCKED'}`")
                            st.markdown(f"**Policy Rationale**: *{last_dec.policy_reason}*")

                    st.markdown("#### Transaction Audit Trail")
                    logs = session.query(AuditLogRecord).filter(AuditLogRecord.transaction_id == selected_tx_id).order_by(AuditLogRecord.timestamp.asc()).all()
                    log_items = [
                        {
                            "Timestamp": l.timestamp.strftime("%Y-%m-%d %H:%M:%S") if l.timestamp else "-",
                            "Event Type": l.event_type,
                            "Severity": l.severity,
                            "Details": json.dumps(l.details_json),
                        }
                        for l in logs
                    ]
                    st.dataframe(pd.DataFrame(log_items), use_container_width=True)
    else:
        st.info("No recovery cases found in database. Use the Interactive Sandbox to evaluate new transactions.")

# TAB 3: Live Interactive Sandbox
with tab3:
    st.subheader("⚡ Live Recovery Sandbox (Buildathon Interactive Demo)")
    st.markdown("Simulate a failed transaction, evaluate AI recovery predictions, apply the deterministic safety policy gate, and execute/verify Razorpay recovery.")

    with st.form("sandbox_form"):
        sb_col1, sb_col2, sb_col3 = st.columns(3)
        with sb_col1:
            tx_id_input = st.text_input("Transaction ID", value="TXN_DEMO_9981")
            amount_input = st.number_input("Transaction Amount (INR)", value=4500.0, min_value=1.0, step=100.0)
            customer_id_input = st.text_input("Customer ID", value="CUST_8832")
        with sb_col2:
            failure_reason_input = st.selectbox(
                "Failure Reason",
                ["network_error", "gateway_timeout", "insufficient_funds", "limit_exceeded", "authentication_failed", "do_not_honor"]
            )
            failure_source_input = st.selectbox("Failure Source", ["bank", "network", "customer", "gateway"])
            payment_method_input = st.selectbox("Payment Method", ["card", "upi", "netbanking", "wallet"])
        with sb_col3:
            historical_success_rate = st.slider("Customer Success Rate", 0.0, 1.0, 0.75, 0.05)
            account_age_days = st.number_input("Account Age (Days)", value=240, min_value=1)
            override_action = st.selectbox("Policy Override (Optional)", ["None (Let AI Select)", "retry", "reminder", "escalation"])

        evaluate_btn = st.form_submit_button("🚀 Run Recovery Pipeline", use_container_width=True)

    if evaluate_btn:
        txn_payload = {
            "transaction_id": tx_id_input,
            "customer_id": customer_id_input,
            "amount": float(amount_input),
            "currency": "INR",
            "status": "failed",
            "failure_reason": failure_reason_input,
            "failure_source": failure_source_input,
            "payment_method": payment_method_input,
            "historical_success_rate": float(historical_success_rate),
            "account_age_days": int(account_age_days),
        }
        
        prop_action = None if override_action.startswith("None") else override_action

        # Run pipeline
        res = recovery_workflow.run(txn_payload, proposed_action=prop_action)
        
        st.success("✅ Recovery Pipeline Executed Successfully")
        
        r_col1, r_col2, r_col3 = st.columns(3)
        with r_col1:
            st.markdown("### 🧠 **1. ML Probabilities**")
            probs = res["decision"]["probabilities"]
            st.markdown(f"- **P(Retry)**: `{probs['retry']:.4f}`")
            st.markdown(f"- **P(Reminder)**: `{probs['reminder']:.4f}`")
            st.markdown(f"- **P(Escalation)**: `{probs['escalation']:.4f}`")
            st.markdown(f"**Optimal Action**: `{res['decision']['selected_action']}`")
            st.markdown(f"**Expected Value**: ₹{res['decision']['expected_value']:,.2f}")

        with r_col2:
            st.markdown("### 🛡️ **2. Policy Gate**")
            allowed = res["decision"]["allowed"]
            badge = "✅ ALLOWED" if allowed else "🚫 BLOCKED"
            st.markdown(f"**Policy Decision**: **{badge}**")
            st.markdown(f"**Risk Tier**: `{res['decision']['risk_level'].upper()}`")
            st.markdown(f"**Policy Reason**: *{res['decision']['reason']}*")

        with r_col3:
            st.markdown("### ⚡ **3. Execution Result**")
            exec_res = res["execution"]
            st.markdown(f"**Execution Status**: `{exec_res['status']}`")
            if exec_res.get("razorpay_order_id"):
                st.markdown(f"**Razorpay Order ID**: `{exec_res['razorpay_order_id']}`")
            st.markdown(f"**Details**: `{json.dumps(exec_res.get('details', {}))}`")

        st.markdown("---")
        st.markdown("### 💳 **4. Razorpay Test Mode Payment Simulation**")
        st.markdown("Simulate the customer completing checkout or failing payment to trigger cryptographic webhook verification:")
        
        sim_col1, sim_col2 = st.columns(2)
        with sim_col1:
            if st.button("Simulate Successful Payment (payment.captured)", key="sim_success"):
                sim_payload = {
                    "event": "payment.captured",
                    "payload": {
                        "payment": {
                            "entity": {
                                "id": f"pay_test_{tx_id_input}",
                                "order_id": exec_res.get("razorpay_order_id") or f"order_{tx_id_input}",
                                "amount": int(round(amount_input * 100)),
                                "currency": "INR",
                                "status": "captured",
                                "notes": {"original_transaction_id": tx_id_input},
                            }
                        }
                    }
                }
                webhook_res = recovery_workflow.process_webhook_event(
                    event_id=f"evt_{tx_id_input}_success",
                    event_type="payment.captured",
                    payload=sim_payload,
                    signature="valid_simulated_sig",
                    raw_body=json.dumps(sim_payload).encode("utf-8")
                )
                st.success(f"🎉 Payment Captured! Verified Recovered Amount: ₹{webhook_res.get('amount_recovered', amount_input):,.2f}")
                st.rerun()

        with sim_col2:
            if st.button("Simulate Failed Payment (payment.failed)", key="sim_fail"):
                sim_payload = {
                    "event": "payment.failed",
                    "payload": {
                        "payment": {
                            "entity": {
                                "id": f"pay_test_{tx_id_input}",
                                "order_id": exec_res.get("razorpay_order_id") or f"order_{tx_id_input}",
                                "amount": int(round(amount_input * 100)),
                                "error_description": "Card declined by issuing bank",
                                "notes": {"original_transaction_id": tx_id_input},
                            }
                        }
                    }
                }
                webhook_res = recovery_workflow.process_webhook_event(
                    event_id=f"evt_{tx_id_input}_failed",
                    event_type="payment.failed",
                    payload=sim_payload,
                    signature="valid_simulated_sig",
                    raw_body=json.dumps(sim_payload).encode("utf-8")
                )
                st.warning("⚠️ Payment Failed event processed. Case status updated to RECOVERY_FAILED.")
                st.rerun()

# TAB 4: Machine-Readable Audit Logs
with tab4:
    st.subheader("📜 Machine-Readable Immutable Audit Logs")
    st.markdown("Every transition, evaluation, policy check, and webhook receipt is recorded with credentials automatically redacted.")
    
    with get_db_session() as session:
        all_logs = session.query(AuditLogRecord).order_by(AuditLogRecord.timestamp.desc()).limit(100).all()
        log_records = [
            {
                "ID": l.id,
                "Timestamp": l.timestamp.strftime("%Y-%m-%d %H:%M:%S") if l.timestamp else "-",
                "Transaction ID": l.transaction_id or "-",
                "Event Type": l.event_type,
                "Severity": l.severity,
                "Sanitized Details": json.dumps(l.details_json),
            }
            for l in all_logs
        ]
    
    if log_records:
        st.dataframe(pd.DataFrame(log_records), use_container_width=True)
    else:
        st.info("No audit logs recorded yet.")
