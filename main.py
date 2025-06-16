import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="Airtel Partner Portal",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ========== PAGE SETUP ==========

home_page = st.Page(
    page="home_page.py",
    title="Home Page",
    icon=":material/home:",
    default=False
)

chat_bot = st.Page(
    page="chatbot.py",
    title=" AI Support",
    icon=":material/support_agent:"
)

l_hub = st.Page(
    page="leave.py",
    title="Leave Management",
    icon=":material/flight_takeoff:"
)

tickets = st.Page(
    page="ticketing.py",
    title="Raise Ticket",
    icon=":material/sell:"
)

# ========== NAVIGATION ==========
page_navigator = st.navigation({
    "Home": [home_page],
    "Help Desk": [chat_bot, tickets],
    "Leave Hub": [l_hub]
})

page_navigator.run()
