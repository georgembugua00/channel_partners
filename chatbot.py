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
    prompt = PromptTemplate(input_variables=["history", "input"], template=template)
    st.session_state.chat_chain = ConversationChain(
        llm=llm,
        memory=st.session_state.memory,
        prompt=prompt
    )

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
