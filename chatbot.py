import streamlit as st
import sqlite3
from datetime import date, timedelta
import pandas as pd
from streamlit_calendar import calendar
import os
import json
import datetime
from PyPDF2 import PdfReader
import streamlit.components.v1 as components
import re
import time
# --- New LLM imports ---
from langchain_ollama import ChatOllama
from langchain.vectorstores import FAISS
from langchain.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import SystemMessage
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate

st.set_page_config(
    page_title="Airtel Partner Portal", 
    layout="wide",
    initial_sidebar_state="expanded",
 )

# --- Initialize LLM + Embeddings ---
@st.cache_resource
def load_ollama_models():
    llm = ChatOllama(model="llama3.2", temperature=0.4)
    embedder = OllamaEmbeddings(model="nomic-embed-text")
    return llm, embedder

llm, embedder = load_ollama_models()

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'tickets' not in st.session_state:
    st.session_state.tickets = []
if 'leaves' not in st.session_state:
    st.session_state.leaves = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'escalated_issues' not in st.session_state:
    st.session_state.escalated_issues = []
if 'nav_choice' not in st.session_state:
    st.session_state.nav_choice = "Home"
if 'Ticketing' not in st.session_state:
    st.session_state.ticket_view = []    

# --- New LLM session state variables ---
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
if "chat_chain" not in st.session_state:
    # Initialize with a simple conversation chain
    template = """You are Lulu, an intelligent AI assistant working at Airtel Kenya. 
    Your job is to support Sales Executives who manage over 200 on-the-ground agents. 
    Help them with operations, float requests, KYC issues, training updates, and urgent tickets. 
    Always respond professionally, concisely, and with context relevant to Airtel's field operations.
    
    Current conversation:
    {chat_history}
    Human: {input}
    Assistant:"""
    prompt = PromptTemplate(input_variables=["chat_history", "input"], template=template)
    st.session_state.chat_chain = ConversationChain(
        llm=llm,
        memory=st.session_state.memory,
        prompt=prompt
    )


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

# Mock Database
USERS = {
    "23188032": {
        "role": "Sales Executive", 
        "name": "Stacy",
        "surname": "Mbugua",
        "email": "george@airtel.com",
        "profile_pic": "https://www.shutterstock.com/image-photo/face-portrait-manager-happy-black-260nw-2278812777.jpg",
        "position": "Sales Executive",
        "managing_partner": "Fine Media",
        "cumulative_leave": 21,
        "used_leave": 6
    },
    "1388231": {
        "role": "Manager", 
        "name": "Bryan Osoro", 
        "email": "john@airtel.com",
        "profile_pic": "https://www.shutterstock.com/image-photo/smiling-cheerful-young-adult-african-260nw-1850821510.jpg" ,
        "position": "Zonal Sales Manager",
        "franchise_type": "On Roll"
    }
}

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

# --- File Processing for RAG ---
def process_file(file):
    docs = []
    if file.name.endswith(".pdf"):
        reader = PdfReader(file)
        raw_text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        docs = [Document(page_content=raw_text)]
    elif file.name.endswith(".csv"):
        df = pd.read_csv(file)
        raw_text = df.to_string()
        docs = [Document(page_content=raw_text)]
    elif file.name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(file)
        raw_text = df.to_string()
        docs = [Document(page_content=raw_text)]

    # Split and embed
    if docs:
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        splits = splitter.split_documents(docs)
        st.session_state.vector_store = FAISS.from_documents(splits, embedder)
        
        # Update RAG chain
        st.session_state.chat_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=st.session_state.vector_store.as_retriever(),
            memory=st.session_state.memory,
            output_key="answer"
        )
        return True
    return False

# --- Authentication ---
def login():
    st.header("Welcome to Saidi Partners Self Care",divider=True)
    with st.form("Login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if username in USERS and password == "airtel123":
                st.session_state.user = USERS[username]
                st.success("Logged in successfully")
                st.rerun()
            else:
                st.error("Invalid credentials")
    return False


# --- Navigation Sidebar ---
def sidebar_navigation():
    st.sidebar.image('../streamlit/images/Airtel-logo.jpg',width=250)
    st.sidebar.title("Navigation")
    menu_options = ["Home", "Leave Management", "AI Support", "Visit Planner", "Profile"]
    if st.session_state.user and st.session_state.user['role'] == "Manager":
        menu_options.append("Manager Dashboard")
    
    for option in menu_options:
        if st.sidebar.button(option):
            st.session_state.nav_choice = option
    
    st.sidebar.title("Knowledge Base")
    with st.sidebar.expander("📄 Upload Document"):
        uploaded_file = st.file_uploader("Upload PDF/CSV/XLSX", 
                                        type=["pdf", "csv", "xlsx", "xls"], 
                                        key="file_upload")
        if uploaded_file:
            if process_file(uploaded_file):
                st.sidebar.success("✅ File indexed! Chat with Lulu about it")
            else:
                st.sidebar.error("Failed to process file")

# --- Leave Roster ---
def leave_roster_calendar():
    st.subheader("📆 My Calender")
    events = []
    for leave in st.session_state.leaves:
        events.append({
            "title": f"{leave.get('name', 'Colleague')} - {leave['type']} Leave",
            "start": leave['start'],
            "end": leave['end'],
            "color": "#ffd700" if leave['status'] == "Pending" else "#00cc00"
        })

    calendar_options = {
        "initialView": "dayGridMonth",
        "editable": True,
        "selectable": False,
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek"
        }
    }
    calendar(events=events, options=calendar_options)            

# --- Profile Summary ---
def profile_summary():
    user = st.session_state.user
    remaining_leave = user['cumulative_leave'] - user['used_leave']
    
    st.html(f"""
    <style>
        .profile-card {{
            background-color: red;
            padding: 20px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            box-shadow: 0 2px 10px rgba(255, 255, 255, 0.1);
        }}
        .profile-img {{
            border-radius: 50%;
            width: 250px;
            height: 250px;
            object-fit: cover;
            margin-right: 20px;
            border: black;
        }}
        .profile-info {{
            flex-grow: 1;
            color:white;
        }}
        .leave-stats {{
            display: flex;
            gap: 20px;
            margin-top: 10px;
        }}
        .leave-card {{
            background-color: #1a1a1a;
            padding: 10px 15px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #333;
            color: white;
        }}
        .leave-card.approved {{
            border-left: 4px solid #00cc00;
        }}
    </style>

    <div class="profile-card">
        <img src="{user.get('profile_pic', 'https://media.istockphoto.com/id/1828923094/photo/portrait-of-happy-woman-with-crossed-arms-on-white-background-lawyer-businesswoman-accountant.jpg?s=2048x2048&w=is&k=20&c=Wg0rEgOUWIC8LSd7L4yqPvqoDaA6CSRGbmlvAc3RZoY=')}" class="profile-img">
        <div class="profile-info">
            <h2>{user['name']} {user.get('surname', '')}</h2>
            <p>📌 {user.get('position', 'Agent')}</p>
            <p>🏢 {user.get('managing_partner', 'Airtel Kenya')}</p>
            <p>🏷️ {user.get('franchise_type', 'Eastleigh')}</p>
            
            <div class="leave-stats">
                <div class="leave-card">
                    <div style="font-size: 1.2em; font-weight: bold;">{user['cumulative_leave']}</div>
                    <div>Cumulative Days</div>
                </div>
                <div class="leave-card">
                    <div style="font-size: 1.2em; font-weight: bold;">{user['used_leave']}</div>
                    <div>Used Days</div>
                </div>
                <div class="leave-card approved">
                    <div style="font-size: 1.2em; font-weight: bold;">{remaining_leave}</div>
                    <div>Remaining Days</div>
                </div>
            </div>
        </div>
    </div>
    """)   

# Create a callback
def callback():
    return f"Ticket Created CR12900"

def ticket_view():
    
        # Timestamp
        time_stamp = int(time.time())
        id_list = ["2001", "2002", "2003"]
        
        name_list = ["Inna", "Maria", "John"]
        
        staffid_list = ["INNAM", "MARIAH", "JOHNS"]
        
        email_list = ["inna@whitecliffe.co.nz", "maria@whitecliffe.co.nz", "john@whitecliffe.co.nz"]
        
        issue_list = ["My monitor stopped working", "Request for a videocamera to conduct webinars", "Password change"]
        
        response = ["Not Yet Provided", "Not Yet Provided", "New password generated: JOJoh"]
        
        ticket_status = ["Open", "Open", "Closed"]
        
        tickets_solved = 0      
        
        
        tickets_solved = 0
        
        for i in range(len(ticket_status)):#    getting all items in the lists in order
            if ticket_status[i-1] == "Closed":
                tickets_solved +=1
        tick_created = int(len(id_list))        
        tick_resolved = int(tickets_solved)
        tick_to_solve = tick_created - tick_resolved
    
        st.header("Ticketing View")
        st.divider()
        # Create Columns
        col1,col2,col3 = st.columns(3)
        with col1:
            st.write("Created Tickets")
            st.markdown(tick_created)
        with col2:    
            st.write("Tickets Resolved")
            st.markdown(tick_resolved)
            
        with col3:    
            st.write("Pending Ticks")
            st.markdown(tick_to_solve)
        conn =  sqlite3.connect("channel_partners_agents.db")
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS channel_partners_tickets(
            issue_text TEXT,
            issue_tag TEXT,
            msisdn INT,
            timestamp TEXT
            )""")
        #user input
        # Create the INSERT FUNCTION
        with st.container():
            with st.form(key='tickets',clear_on_submit=True,border=True):
                issue_text = st.text_input("Type the Issue")
                issue_tag = st.selectbox(label='Tag the Ticket',options=("Network","Airtel Money",'Bundles','Float','KYC','Float Problem',"Commission Not Received"))
                msisdn = st.text_input(label="Enter Agent MSISDN",max_chars=10)
                time_stamp = time_stamp
                submit = st.form_submit_button(label="Create a Ticket")
                
                if submit:
                    if issue_text:
                        cursor.execute(f"""INSERT INTO channel_partners_tickets (issue_text,issue_tag,msisdn,time_stamp) VALUES (?,?,?,?)
                        """,(issue_text,issue_tag,msisdn,time_stamp))
                        conn.commit()
                        st.success(body="Ticket Successfully created",icon='🔥')
                    else:
                        st.write("Kindly make sure all Fields are filled out!!")    
                    

            
            

    

# --- Home Page ---
def home_page():
    st.header("Channel Partner Management System")
    st.markdown("---")
    profile_summary()
    st.subheader("📢 Latest Offers")
    components.html(slideshow_html, height=500)
    leave_roster_calendar()

# --- Leave Management ---
def leave_management():
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

# --- AI Chatbot ---
def chatbot():
    st.header("🤖 Airtel AI Assistant - Lulu")
    inject_custom_css()

    # Theme toggle
    theme = st.radio("Choose Theme", ["Light", "Dark"], horizontal=True)
    if theme == "Dark":
        st.markdown("""<style>body { background-color: #121212; color: white; }</style>""", unsafe_allow_html=True)

    # Initialize chat history
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # Display chat history
    for msg in st.session_state.chat_messages:
        div_class = "user-message" if msg["role"] == "user" else "bot-message"
        timestamp = f'<div class="timestamp">{msg["timestamp"]}</div>'
        st.markdown(f"""
        <div class="chat-box">
            <div class="chat-message {div_class}">
                {msg["content"]}
            </div>
            {timestamp}
        </div>
        """, unsafe_allow_html=True)

    # Quick actions
    if len(st.session_state.chat_messages) == 0:
        st.subheader('Quick Actions')
        col1, col2 = st.columns(2)
        quick_responses = ["KYC Approval", "Float Issues", "Create a Ticket", "Onboarding Steps", "Follow Up on Ticket"]
        with col1:
            for response in quick_responses[:2]:
                if st.button(response):
                    handle_user_input(response)
        with col2:
            for response in quick_responses[2:]:
                if st.button(response):
                    handle_user_input(response)

    # Chat input
    user_input = st.chat_input("Ask a question...")
    if user_input:
        handle_user_input(user_input)

    # Export Chat
    if st.button("📄 Export Chat as JSON"):
        with open("chat_history.json", "w") as f:
            json.dump(st.session_state.chat_messages, f, indent=2)
        st.success("Chat history exported to chat_history.json ✅")

def parse_thoughts(response_text):
    # Extract text inside <think>...</think>
    match = re.search(r"<think>(.*?)</think>", response_text, re.DOTALL)
    if match:
        thought = match.group(1).strip()
        cleaned_response = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL).strip()
        return thought, cleaned_response
    return None, response_text


# Load shop data from JSON file
with open("/Users/danielwanganga/Documents/ChatBot/shop_location.json", "r") as f:
    SHOP_LOCATIONS = json.load(f)

def find_shop_by_keyword(query):
    for shop_name, shop_data in SHOP_LOCATIONS.items():
        if shop_name.lower() in query.lower():
            return shop_data
    return None

def format_shop_info(shop_data):
    name = shop_data.get("SHOP NAME", "N/A")
    location = shop_data.get("PHYSICAL LOCATION", "N/A")
    plus_code = shop_data.get("Plus Code", "")
    lat = shop_data.get("Latitude")
    lon = shop_data.get("Longitude")
    maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}" if lat and lon else ""
    return f"**{name}**\n📍 {location}\n🕒 {shop_data.get('Business Hours', '')}\n🌍 [View on Maps]({maps_link})"

def is_shop_query(user_input):
    keywords = ["shop", "location", "nearest shop", "where can I find"]
    return any(k in user_input.lower() for k in keywords)

def handle_user_input(user_input):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Add user message to history
    st.session_state.chat_messages.append({
        "role": "user",
        "content": user_input,
        "timestamp": timestamp
    })
    
    with st.spinner("Thinking..."):
        # Determine which input key to use based on chain type
        if st.session_state.vector_store:
            # Using ConversationalRetrievalChain - requires "question" key
            inputs = {"question": user_input}
        else:
            # Using ConversationChain - requires "input" key
            inputs = {"input": user_input}
            
        result = st.session_state.chat_chain.invoke(inputs)

        # Handle both output types gracefully
        if 'answer' in result:
            response = result['answer']
        elif 'response' in result:
            response = result['response']
        else:
            response = str(result)  # fallback

        # Parse thoughts if any
        thought, cleaned_response = parse_thoughts(response)
        if thought:
            with st.expander("🤖 Internal reasoning"):
                st.markdown(thought)
            response = cleaned_response
            
        if user_input:
            if is_shop_query(user_input):
                shop_data = find_shop_by_keyword(user_input)
                if shop_data:
                    st.markdown(format_shop_info(shop_data))
                else:
                    st.write("Sorry, we couldn’t find a matching shop. Try specifying the town or shop name.")


    # Add assistant response to history
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.chat_messages.append({
        "role": "assistant",
        "content": response,
        "timestamp": timestamp
    })
    
    # Refresh to show new messages
    st.rerun()

    # Escalate if needed
    if "sorry" in response.lower() or "unable" in response.lower():
        st.warning("Escalating to support team.")
        if "escalated_issues" not in st.session_state:
            st.session_state.escalated_issues = []
        st.session_state.escalated_issues.append({
            "query": user_input,
            "status": "Pending",
            "response": response
        })


# --- Profile Settings ---
def profile():
    st.header("Profile")
    st.subheader("Personal Information")
    st.write(f"Name: {st.session_state.user['name']}")
    st.write(f"Role: {st.session_state.user['role']}")
    with st.expander("Contact Information"):
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Primary Contact", key='primary_contact')
            st.text_input("Phone Number", key='primary_phone')
        with col2:
            st.text_input("Secondary Contact", key='secondary_contact')
            st.text_input("Phone Number", key='secondary_phone')
    with st.expander("Preferences"):
        st.selectbox("Theme", ["Light", "Dark"], key='theme')
        st.selectbox("Language", ["English", "Swahili"], key='language')

# --- Manager Dashboard ---
def manager_dashboard():
    st.header("Sales Executive Dashboard")
    
    # Pending Approvals Section
    st.subheader("⏳ Pending Approvals")
    pending_leaves = [l for l in st.session_state.leaves if l['status'] == "Pending"]
    
    if not pending_leaves:
        st.info("No pending leave requests")
    else:
        for leave in pending_leaves:
            with st.container():
                cols = st.columns([5, 2, 2])
                with cols[0]:
                    st.markdown(f"""
                    **{leave['type']} Leave**  
                    🗓️ {leave['start']} to {leave['end']}  
                    📝 {leave['description']}
                    """)
                
                with cols[1]:
                    if st.button(f"✅ Approve", key=f"approve_{leave['id']}"):
                        leave['status'] = "Approved"
                        leave['comments'] = "Approved by manager"
                        st.rerun()
                
                with cols[2]:
                    if st.button(f"❌ Reject", key=f"reject_{leave['id']}"):
                        st.session_state['rejecting_id'] = leave['id']
                    
                if 'rejecting_id' in st.session_state and st.session_state['rejecting_id'] == leave['id']:
                    comment = st.text_input("Reason for rejection", key=f"comment_{leave['id']}")
                    if st.button("Submit Rejection"):
                        leave['status'] = "Rejected"
                        leave['comments'] = comment
                        del st.session_state['rejecting_id']
                        st.rerun()

    # Approved Leaves Section
    st.subheader("✅ Approved Leaves")
    approved_leaves = [l for l in st.session_state.leaves if l['status'] == "Approved"]
    
    if not approved_leaves:
        st.info("No approved leaves")
    else:
        for leave in approved_leaves:
            with st.container():
                st.markdown(f"""
                <div style="padding:10px; border-left:4px solid #00cc00; margin:5px 0;">
                    📌 **{leave['type']} Leave**  
                    🗓️ {leave['start']} to {leave['end']}  
                    📝 {leave['description']}  
                    💬 *{leave.get('comments', 'No comments')}*
                </div>
                """, unsafe_allow_html=True)

    # Declined Leaves Section
    st.subheader("❌ Declined Leaves")
    declined_leaves = [l for l in st.session_state.leaves if l['status'] == "Rejected"]
    
    if not declined_leaves:
        st.info("No declined leaves")
    else:
        for leave in declined_leaves:
            with st.container():
                st.markdown(f"""
                <div style="padding:10px; border-left:4px solid #ff4b4b; margin:5px 0;">
                    📌 **{leave['type']} Leave**  
                    🗓️ {leave['start']} to {leave['end']}  
                    📝 {leave['description']}  
                    🔴 **Reason:** {leave.get('comments', 'No reason provided')}
                </div>
                """, unsafe_allow_html=True)

    # Performance Section
    st.subheader("📊 Cluster Performance")
    performance_data = pd.DataFrame({
        "Agent": ["Daniel Mbugua", "Michael Jackson", "John Nzuve"],
        "Sales": [45, 32, 67],
        "KYC Completed": [23, 15, 34]
    })
    st.bar_chart(performance_data.set_index("Agent"))

# --- Slideshow Component ---
slideshow_html = """
<div class="slideshow-container">
  <div class="mySlides fade">
    <img src="https://cdn-webportal.airtelstream.net/website/kenya/assets/images/opco/offers/Send-Money-for%20Free-Web%20Banners.jpg" style="width:100%; height:auto;">
  </div>
  <div class="mySlides fade">
    <img src="https://cdn-webportal.airtelstream.net/website/kenya/assets/images/opco/offers/2GB-@-99-Bob-web-banners.jpg" style="width:100%; height:auto;">
  </div>
  <div class="mySlides fade">
    <img src="https://cdn-webportal.airtelstream.net/website/kenya/assets/images/opco/offers/1GB-@15-Bob-web-banners.jpg" style="width:100%; height:auto;">
  </div>
  <div class="mySlides fade">
    <img src="https://cdn-webportal.airtelstream.net/website/kenya/assets/images/AIRTEL-KENYA_HVC_CAMPAIGN_700_by_700_1.jpg" style="width:100%; height:50%;">
</div>
<div style="text-align:center">
  <span class="dot"></span> 
  <span class="dot"></span> 
  <span class="dot"></span> 
</div>
<script>
let slideIndex = 0;
showSlides();
function showSlides() {
  let i;
  let slides = document.getElementsByClassName("mySlides");
  let dots = document.getElementsByClassName("dot");
  for (i = 0; i < slides.length; i++) {
    slides[i].style.display = "none";  
  }
  slideIndex++;
  if (slideIndex > slides.length) {slideIndex = 1}    
  for (i = 0; i < dots.length; i++) {
    dots[i].className = dots[i].className.replace(" active", "");
  }
  slides[slideIndex-1].style.display = "block";  
  dots[slideIndex-1].className += " active";
  setTimeout(showSlides, 5000);
}
</script>
<style>
.slideshow-container { max-width: 1000px; position: relative; margin: auto; }
.mySlides { display: none; }
.dot { height: 15px; width: 15px; margin: 0 2px; background-color: #bbb; border-radius: 50%; display: inline-block; }
.active { background-color: #717171; }
.fade { animation-name: fade; animation-duration: 1.5s; }
@keyframes fade { from {opacity: .4} to {opacity: 1} }
</style>
"""

# --- Main App Logic ---
if not st.session_state.user:
    login()
else:
    sidebar_navigation()
    if st.session_state.nav_choice == "Home":
        home_page()
    elif st.session_state.nav_choice == "Leave Management":
        leave_management()
    elif st.session_state.nav_choice == "AI Support":
        chatbot()
    elif st.session_state.nav_choice == "Profile":
        profile()
    #elif st.session_state.nav_choice == "Ticketing":
    #    ticket_view()
    elif (st.session_state.nav_choice == "Manager Dashboard" and 
          st.session_state.user['role'] == "Manager"):
        manager_dashboard()

# --- Footer ---
st.markdown("---")
st.markdown("**Airtel Partner Portal** | © 2025 Airtel Kenya")



