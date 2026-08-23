import streamlit as st
from PIL import Image
import pandas as pd
import json

st.set_page_config(page_title="Brite Spark 2026 Dashboard", layout="wide")

# Header Section
st.title("⚡ Brite Spark 2026 — System Analytics Dashboard")
st.markdown("### Delivery Metrics & Regulatory Compliance Tracking (Direction CR-2026/11)")
st.divider()

# Top KPI Metric Cards
col1, col2, col3, col4 = st.columns(4)
col1.metric("Successful Reaches", "744", "79.1% Total")
col2.metric("Rate Limit Blocked", "196", "CR-2026/11 Compliant", delta_color="inverse")
col3.metric("Opt-Outs Blocked", "89", "Privacy Safeguard")
col4.metric("Fallback Retries", "287", "Multi-Channel Logic")

st.divider()

# Display Generated Charts Side-by-Side
st.subheader("📊 System Visualizations")
img_col1, img_col2 = st.columns(2)

with img_col1:
    st.image("metrics_summary.png", caption="System Delivery & Compliance Overview", use_column_width=True)

with img_col2:
    st.image("outcomes_pie.png", caption="Appointment Outcome Distribution", use_column_width=True)

st.divider()

# Audit Log Preview Section
st.subheader("📜 Outbox Audit Log Preview (`outbox.jsonl`)")
try:
    data = []
    with open("outbox.jsonl", "r") as f:
        for i, line in enumerate(f):
            if i >= 10:  # Display first 10 entries
                break
            data.append(json.loads(line))
    st.dataframe(pd.DataFrame(data), use_container_width=True)
except Exception:
    st.info("Run `python main.py` first to generate the audit log.")