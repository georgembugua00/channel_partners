import streamlit as st
from sales_exec.user_data import  USERS

if 'user' not in st.session_state:
    st.session_state.user = None
    
  

def profile_summary():
    
    if "user" not in st.session_state:
        username = st.text_input("Enter your username")
    if username and username in USERS:
        st.session_state.user = USERS['username']
        st.success(f"Welcome, {USERS['username']['name']}!")
        st.rerun()
    elif username:
        st.error("User not found.")
    
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