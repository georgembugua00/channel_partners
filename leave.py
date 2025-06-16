
import streamlit as st
from streamlit_calendar import calendar
import datetime  




# --- Partner-Specific Leave Policies (Example: Fine Media) ---
LEAVE_POLICIES = {
    "Annual": {"max_days": 21},
    "Sick": {"max_days": 14, "full_pay_days": 7},
    "Maternity": {"max_days": 90},
    "Paternity": {"max_days": 14},
    "Study": {"max_days": 30},
    "Compassionate": {"max_days": 10},
    "Unpaid": {"max_days": 365},
}


# --- Helper: Generate recurring partner visit events ---
def generate_partner_visit_events(start_date, location="Mathare", total_visits=50):
    visits_per_day = 10
    visit_days = 5  # Monday to Friday
    events = []

    for i in range(visit_days):
        visit_date = start_date + timedelta(days=i)
        events.append({
            "title": f"Visit {visits_per_day} Partners - {location}",
            "start": visit_date.strftime("%Y-%m-%dT09:00:00"),
            "end": visit_date.strftime("%Y-%m-%dT17:00:00"),
            "color": "#1e90ff"
        })
    return events

# --- Leave Roster + Task Calendar ---
def leave_roster_calendar():
    st.subheader("📆 My Calendar")

    if 'leaves' not in st.session_state:
        st.session_state.leaves = []

    # Add existing leave events
    events = []
    for leave in st.session_state.leaves:
        events.append({
            "title": f"{leave.get('name', 'Colleague')} - {leave['type']} Leave",
            "start": leave['start'],
            "end": leave['end'],
            "color": "#ffd700" if leave.get('status') == "Pending" else "#00cc00"
        })

    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday

    # Add recurring weekly task: visiting channel partners
    events.extend(generate_partner_visit_events(start_of_week))

    # Dynamic UI options
    default_view = st.selectbox("Default View", ["dayGridMonth", "timeGridWeek"])
    editable = st.checkbox("Allow Editing", value=True)
    selectable = st.checkbox("Allow Selecting", value=True)

    calendar_options = {
        "initialView": default_view,
        "editable": editable,
        "selectable": selectable,
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek"
        }
    }

    # Render Calendar
    calendar(events=events, options=calendar_options)


# Custom CSS for UI styling
def inject_custom_css():
    st.markdown("""
    <style>
        .profile-card {
            background-color: red;
            padding: 20px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            box-shadow: 0 2px 10px rgba(255, 255, 255, 0.1);
        }
        .chat-message {
            border-radius: 12px;
            padding: 10px 15px;
            margin: 10px 0;
            max-width: 75%;
            word-wrap: break-word;
        }
        .user-message {
            background-color: #e0e0e0;
            color: black;
            align-self: flex-end;
            margin-left: auto;
        }
        .bot-message {
            background-color: #f44336;
            color: white;
            align-self: flex-start;
            margin-right: auto;
        }
        .timestamp {
            font-size: 0.75em;
            color: #999;
            text-align: right;
            margin-top: 4px;
        }
        .chat-box {
            display: flex;
            flex-direction: column;
        }
    </style>
    <script>
        const chatContainer = window.parent.document.querySelector('.main');
        if (chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight;
    </script>
    """, unsafe_allow_html=True)
    

# --- Leave Management ---
def leave_management():
    if 'leaves' not in st.session_state:
        st.session_state.leaves = []
        
    st.title("📝 Leave Management")
    leave_tabs = st.tabs(["Apply Leave", "Withdraw Leave", "Leave History", "Leave Planner"])

    # --- Apply Leave ---
    with leave_tabs[0]:
        st.header("Apply for Leave")
        leave_type = st.selectbox("Select Leave Type", list(LEAVE_POLICIES.keys()))
        start = st.date_input("Start Date", min_value=date.today())
        end = st.date_input("End Date", min_value=start)
        description = st.text_area("Reason for Leave")

        attachment_required = leave_type in ["Sick", "Maternity", "Paternity", "Compassionate"]
        attachment = st.file_uploader("Upload Attachment", type=['pdf', 'jpg', 'png']) if attachment_required else None

        leave_days_taken = (end - start).days + 1
        remaining_days = LEAVE_POLICIES[leave_type]['max_days'] - leave_days_taken

        st.info(f"**Total Leave Days 2025**: {LEAVE_POLICIES[leave_type]['max_days']}")
        st.warning(f"**Days Taken**: {leave_days_taken}")
        st.success(f"**Remaining**: {remaining_days}")

        if st.button("Apply Leave"):
            st.session_state.leaves.append({
                "type": leave_type,
                "start": start,
                "end": end,
                "description": description,
                "attachment": bool(attachment),
                "status": "Pending"
            })
            st.success("Leave request submitted successfully!")

    # --- Withdraw Leave ---
    with leave_tabs[1]:
        st.header("Withdraw Leave Request")
        for i, leave in enumerate(st.session_state.leaves):
            if leave['status'] == "Pending":
                with st.expander(f"{leave['type']} Leave: {leave['start']} to {leave['end']}"):
                    st.markdown(f"**Reason**: {leave['description']}")
                    withdraw_reason = st.selectbox("Reason for Withdrawal", ["Change of Plan", "Emergency", "Other"], key=f"withdraw{i}")
                    if withdraw_reason == "Other":
                        custom_reason = st.text_area("Please Specify", key=f"custom{i}")
                        withdraw_reason = custom_reason
                    if st.button("Withdraw Leave", key=f"button{i}"):
                        leave['status'] = "Withdrawn"
                        st.session_state.withdraw_requests.append({"leave": leave, "reason": withdraw_reason})
                        st.success("Leave request withdrawn.")

    # --- Leave History ---
    with leave_tabs[2]:
        st.header("Leave History")
        filter_type = st.selectbox("Filter By", ["All"] + list(LEAVE_POLICIES.keys()) + ["Approved", "Declined", "Withdrawn"])

        for leave in st.session_state.leaves:
            if filter_type != "All" and filter_type not in [leave['type'], leave['status']]:
                continue
            st.markdown(f"""
            <div class='card {leave['status'].lower()}'>
                <h4>{leave['type']} Leave ({leave['status']})</h4>
                <p>{leave['start']} to {leave['end']}</p>
                <p>{leave['description']}</p>
            </div>
            """, unsafe_allow_html=True)

    # --- Leave Planner ---
    with leave_tabs[3]:
        st.header("AI-Powered Leave Planner 🧠")
        total_days = st.number_input("How many leave days do you want to use?", min_value=1, max_value=30)
        spread_days = st.number_input("Over how many days should they be spread?", min_value=1, max_value=60)
        deadlines = st.text_area("List any important deadlines during that period")
        emergency_contact = st.text_input("Emergency Contact Person and Number")
        task_info = st.text_area("List any ongoing tasks or projects")
        delegated_to = st.text_input("Who will pick up your tasks?")
        notes = st.text_area("Any notes for task handover")
        events = st.text_input("Any events you're planning to attend?")

        if st.button("Generate Plan"):
            leave_plan = {
                "id": len(st.session_state.leaves)+1,
                "start_date": date.today() + timedelta(days=2),
                "end_date": date.today() + timedelta(days=2+total_days-1),
                "days": total_days
            }
            delegation_plan = {
                "task": task_info,
                "delegate": delegated_to,
                "notes": notes
            }
            st.success("✅ Plan Generated")
            st.write("### 🗓️ Leave Schedule")
            st.json(leave_plan)
            st.write("### 🧾 Task Delegation")
            st.json(delegation_plan)
            st.warning("📌 Once done, don't forget to save and submit your plan.")    
            
leave_management()            
