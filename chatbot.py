import streamlit as st
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
from PyPDF2 import PdfReader
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from sentence_transformers import SentenceTransformer
import json
import pandas as pd
import re
import datetime
import os
# --- Initialize LLM + Embeddings ---



@st.cache_resource
def load_ollama_models():
    
    llm = ChatOllama(model='llama3')
    
    if "memory" not in st.session_state:
        st.session_state.memory = ConversationBufferMemory(return_messages=True)
    
    embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return llm, None, embedder

# ✅ Make sure to call it BEFORE using `llm`
llm, minicpm, embedder = load_ollama_models()


# --- Custom CSS for UI styling ---
def inject_custom_css():
    st.html("""
    <style>
        /* General styling for the app */
        .stApp {
            background-color: #000000; /* Black background for the entire app */
            color: #F0F0F0; /* Light grey text for the entire app */
            font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        }

        /* Header styling */
        h1, h2, h3, h4, h5, h6 {
            color: #FF4B4B; /* Airtel-like red for headers */
        }

        /* Chat container styling */
        .chat-container {
            display: flex;
            flex-direction: column;
            gap: 15px; /* Space between messages */
            padding: 10px;
            max-height: 70vh; /* Limit height to enable scrolling */
            overflow-y: auto; /* Enable vertical scrolling */
            border-radius: 10px;
            background-color: #333333; /* Dark grey background for chat area */
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4); /* More prominent shadow on dark background */
        }

        /* Individual chat message styling */
        .chat-message {
            border-radius: 18px; /* More rounded corners */
            padding: 12px 18px;
            max-width: 80%; /* Slightly wider max-width */
            word-wrap: break-word;
            line-height: 1.5;
            display: flex; /* Use flexbox to arrange content and timestamp */
            flex-direction: column; /* Stack content and timestamp vertically */
            position: relative; /* Keep relative for potential future absolute elements */
        }

        /* User message styling */
        .user-message {
            background-color: #2c2c2c; /* Darker grey for user messages */
            color: #FFFFFF; /* White text for user messages */
            align-self: flex-end;
            margin-left: auto;
            border-bottom-right-radius: 4px; /* Tail effect */
        }

        /* Bot message styling */
        .bot-message {
            background-color: #FF4B4B; /* Red for bot messages */
            color: white; /* White text for better contrast on red */
            align-self: flex-start;
            margin-right: auto;
            border-bottom-left-radius: 4px; /* Tail effect */
        }

        /* Timestamp styling */
        .timestamp {
            font-size: 0.7em;
            color: rgba(255, 255, 255, 0.7); /* Lighter transparent white for user on dark background */
            margin-top: 5px; /* Space between message content and timestamp */
            align-self: flex-end; /* Align timestamp to the right within the message bubble */
        }
        .bot-message .timestamp {
            color: rgba(255, 255, 255, 0.8); /* Slightly more opaque white for bot on red background */
            align-self: flex-start; /* Align timestamp to the left within the bot message bubble */
        }

        /* Quick actions styling */
        .stButton>button {
            background-color: #FF4B4B; /* Red buttons */
            color: white;
            border-radius: 8px;
            border: none;
            padding: 10px 15px;
            font-size: 1em;
            margin: 5px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
            transition: background-color 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #E03E3E; /* Darker red on hover */
        }

        /* Input area styling */
        .stTextInput>div>div>input {
            border-radius: 20px;
            padding: 10px 15px;
            border: 1px solid #555555; /* Darker grey border for inputs */
            background-color: #1a1a1a; /* Dark background for input field */
            color: #f0f0f0; /* Light text color for input field */
        }
        .stFileUploader>div>button {
            background-color: #007BFF; /* Blue for upload */
            color: white;
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 0.9em;
        }

        /* Scroll to bottom of chat */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        /* Custom scrollbar for chat container */
        .chat-container::-webkit-scrollbar {
            width: 8px;
        }
        .chat-container::-webkit-scrollbar-track {
            background: #222222; /* Dark track */
            border-radius: 10px;
        }
        .chat-container::-webkit-scrollbar-thumb {
            background: #555555; /* Grey thumb */
            border-radius: 10px;
        }
        .chat-container::-webkit-scrollbar-thumb:hover {
            background: #777777;
        }

    </style>
    <script>
        // Scroll to the bottom of the chat on new messages
        function scrollToBottom() {
            const chatContainer = window.parent.document.querySelector('.chat-container');
            if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        }
        // Call it after the page loads or updates
        window.onload = scrollToBottom;
        window.parent.document.addEventListener('DOMContentLoaded', scrollToBottom);
    </script>
    """)

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

# ---- HELPER FUNCTIONS ----
def parse_thoughts(response_text):
    # Extract text inside <think>...</think>
    match = re.search(r"<think>(.*?)</think>", response_text, re.DOTALL)
    if match:
        thought = match.group(1).strip()
        cleaned_response = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL).strip()
        return thought, cleaned_response
    return None, response_text

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
        if st.session_state.get("vector_store", None):
            # Using ConversationalRetrievalChain - requires "question" key
            inputs = {"question": user_input}
        else:
            # Using ConversationChain - requires "input" key
            inputs = {"input": user_input}
            
        result = st.session_state.chat_chain.invoke(inputs)

        # Handle both output types gracefully
        if isinstance(result, dict):
            response = result.get('answer') or result.get('response') or str(result)
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

# ---- OPTIONAL: Add your custom CSS injection function here ----
def inject_custom_css():
    # Insert your styling here if needed
    pass

# ---- RUN APP ----
chatbot()



