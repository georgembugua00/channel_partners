import json
import os
import uuid
import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd

# -------------- Simulated OCR & MiniCPM-V Reasoning ------------------
def minicipm_ocr_pipeline(image_bytes):
    # Simulate OCR output from image
    extracted_text = "Transaction failed due to insufficient float."
    # Simulate reasoning/tagging by MiniCPM-V
    description = extracted_text
    tag = "Float"
    return description, tag

# ---------------- Ticketing System ------------------
def ticket_view():
    st.header("🎫 Partner Ticket Dashboard")
    st.divider()

    # Database connection
    conn = sqlite3.connect("/Users/danielwanganga/Documents/Channel Partner/streamlit/channel_partners_agents.db", check_same_thread=False)
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channel_partners_tickets (
            ticket_id TEXT PRIMARY KEY,
            agent_msisdn TEXT,
            issue_text TEXT,
            issue_tag TEXT,
            status TEXT,
            level TEXT,
            assigned_to TEXT,
            image_path TEXT,
            created_at TEXT,
            last_updated TEXT
        )
    """)

    # Stats
    df_all = pd.read_sql_query("SELECT * FROM channel_partners_tickets", conn)
    total = len(df_all)
    resolved = df_all[df_all["status"] == "Closed"].shape[0]
    pending = total - resolved

    col1, col2, col3 = st.columns(3)
    col1.metric("Created Tickets", total)
    col2.metric("Resolved", resolved)
    col3.metric("Pending", pending)

    # ---------------- Ticket Creation Form ------------------
    st.divider()
    st.subheader("📨 Raise a Ticket")
    with st.form("ticket_form", clear_on_submit=True):
        msisdn = st.text_input("📱 Agent MSISDN")
        uploaded_image = st.file_uploader("📎 Upload Screenshot (Optional)", type=["png", "jpg", "jpeg"])

        auto_description, auto_tag = "", ""
        if uploaded_image:
            auto_description, auto_tag = minicipm_ocr_pipeline(uploaded_image.read())

        issue_text = st.text_area("📝 Issue Description", value=auto_description)
        issue_tag = st.selectbox("🏷️ Tag", ["Float", "SIM Swap", "KYC", "Commission", "Network", "Training", "Other"], index=0 if not auto_tag else ["Float", "SIM Swap", "KYC", "Commission", "Network", "Training", "Other"].index(auto_tag))
        submit = st.form_submit_button("✅ Submit Ticket")

        if submit:
            if msisdn and issue_text:
                ticket_id = str(uuid.uuid4())[:8]
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                image_path = ""

                if uploaded_image:
                    os.makedirs("uploads", exist_ok=True)
                    image_path = f"uploads/{ticket_id}_{uploaded_image.name}"
                    with open(image_path, "wb") as f:
                        f.write(uploaded_image.read())

                conn.execute("""
                    INSERT INTO channel_partners_tickets (ticket_id, agent_msisdn, issue_text, issue_tag, status, level, assigned_to, image_path, created_at, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (ticket_id, msisdn, issue_text, issue_tag, "Open", "L0", "Intern", image_path, timestamp, timestamp))
                conn.commit()
                st.success(f"✅ Ticket #{ticket_id} submitted!")
            else:
                st.warning("⚠️ Please provide Agent MSISDN and Issue description.")

    # ---------------- Ticket Viewer ------------------
    st.divider()
    st.subheader("📋 Submitted Tickets")
    df = pd.read_sql_query("SELECT * FROM channel_partners_tickets ORDER BY last_updated DESC", conn)

    if not df.empty:
        status_filter = st.multiselect("Filter by Status", df["status"].unique(), default=df["status"].unique())
        level_filter = st.multiselect("Filter by Level", df["level"].unique(), default=df["level"].unique())
        filtered_df = df[df["status"].isin(status_filter) & df["level"].isin(level_filter)]
        st.dataframe(filtered_df)

        # Escalation block
        st.subheader("🚀 Escalate a Ticket")
        ticket_to_escalate = st.selectbox("Select Ticket", filtered_df["ticket_id"].tolist())
        new_level = st.selectbox("Escalate to", ["L1", "L2"])
        if st.button("Escalate"):
            assigned_to = "Shelia" if new_level == "L1" else "Caroline"
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("""
                UPDATE channel_partners_tickets
                SET level = ?, assigned_to = ?, status = ?, last_updated = ?
                WHERE ticket_id = ?
            """, (new_level, assigned_to, "Escalated", now, ticket_to_escalate))
            conn.commit()
            st.success(f"✅ Ticket #{ticket_to_escalate} escalated to {new_level}.")
    else:
        st.info("No tickets found.")


ticket_view()