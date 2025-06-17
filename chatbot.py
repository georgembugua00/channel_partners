import streamlit as st
from langchain_ollama import ChatOllama
from langchain_community.vectorstores import FAISS # Updated import to langchain_community
from langchain_community.embeddings import OllamaEmbeddings # Updated import to langchain_community
from langchain.text_splitter import RecursiveCharacterTextSplitter # Keep if using RAG later, otherwise can remove
from langchain.docstore.document import Document # Keep if using RAG later
from langchain.chains import ConversationalRetrievalChain # Keep if using RAG later
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import SystemMessage
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
from PyPDF2 import PdfReader # Keep if using PDF processing later
import json
import pandas as pd
import re
import datetime
import httpx
from ollama import Client # For direct Ollama client operations like listing models

# --- Ollama Configuration ---
# Define Ollama Configuration globally as they are constants
@st.cache_resource
def init_llm_and_memory():
    # Define models to be used (ChatOllama and OllamaEmbeddings will default to localhost:11434)
    TEXT_MODEL = "llama3.2"
    EMBED_MODEL = "nomic-embed-text"

    # Initialize Ollama LLM for general text conversations
    llm = ChatOllama(model=TEXT_MODEL, temperature=0.4)

    # Initialize Ollama embeddings
    embedder = OllamaEmbeddings(model=EMBED_MODEL)
    
    # Removed: All server connection and model availability checks for simplicity
    # The application will now directly attempt to use the models.
    # Connection errors will be caught in handle_user_input.

    return llm, embedder # Return only llm and embedder

# Use the new function name
llm, embedder = init_llm_and_memory()


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

# --- Helper functions for parsing and data loading ---
def parse_thoughts(response_text):
    # Extract text inside <think>...</think>
    match = re.search(r"<think>(.*?)</think)", response_text, re.DOTALL)
    if match:
        thought = match.group(1).strip()
        cleaned_response = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL).strip()
        return thought, cleaned_response
    return None, response_text

# Load shop data from JSON file (ensure this path is correct on your system)
try:
    with open("shop_location.json", "r") as f:
        SHOP_LOCATIONS = json.load(f)
except FileNotFoundError:
    st.error("Error: 'shop_location.json' not found. Please ensure the file exists at the specified path.")
    SHOP_LOCATIONS = {} # Initialize as empty to prevent further errors

def find_shop_by_keyword(query):
    for shop_name, shop_data in SHOP_LOCATIONS.items():
        if shop_name.lower() in query.lower():
            return shop_data
    return None

def format_shop_info(shop_data):
    name = shop_data.get("SHOP NAME", "N/A")
    location = shop_data.get("PHYSICAL LOCATION", "N/A")
    # plus_code = shop_data.get("Plus Code", "") # Not used in output
    lat = shop_data.get("Latitude")
    lon = shop_data.get("Longitude")
    # Corrected Google Maps link format
    maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}" if lat and lon else ""
    return f"**{name}**\n📍 {location}\n🕒 {shop_data.get('Business Hours', '')}\n🌍 [View on Maps]({maps_link})"

def is_shop_query(user_input):
    keywords = ["shop", "location", "nearest shop", "where can I find", "shop near me"]
    return any(k in user_input.lower() for k in keywords)

# --- REMOVED: OCR/Visual Reasoning with MiniCPM function ---
# The analyze_image_with_minicpm function is removed as vision model logic is no longer used.

# --- New LLM session state variables (moved to global scope) ---
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
if "chat_chain" not in st.session_state:
    template = """You are Lulu, an intelligent AI assistant working at Airtel Kenya. \
    Your job is to support Sales Executives who manage over 200 on-the-ground agents. \
    Help them with operations, float requests, KYC issues, training updates, and urgent tickets. \
    Always respond professionally, concisely, and with context relevant to Airtel's field operations.

    Current conversation:
    {chat_history}
    Human: {input}
    Assistant:"""
    prompt = PromptTemplate(input_variables=["chat_history", "input"], template=template)
    st.session_state.chat_chain = ConversationChain(
        llm=llm, # This is the ChatOllama instance
        memory=st.session_state.memory,
        prompt=prompt,
        memory_key="chat_history" # Corrected memory key, though now redundant as Memory will set it.
    )

def handle_user_input(user_input):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Add user message to history
    st.session_state.chat_messages.append({
        "role": "user",
        "content": user_input,
        "timestamp": timestamp
    })

    with st.spinner("Lulu is thinking..."):
        # For ConversationChain, it always expects 'input'
        inputs = {"input": user_input}

        try:
            result = st.session_state.chat_chain.invoke(inputs)

            # Handle both output types gracefully (ChatOllama usually returns AIMessage which has .content)
            response = result.content if hasattr(result, 'content') else str(result)

            # Parse thoughts if any
            thought, cleaned_response = parse_thoughts(response)
            if thought:
                with st.expander("🤖 Internal reasoning"):
                    st.markdown(thought)
                response = cleaned_response

            # Add bot message to history
            st.session_state.chat_messages.append({
                "role": "bot",
                "content": response,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            # Special handling for shop queries after LLM response
            if is_shop_query(user_input):
                shop_data = find_shop_by_keyword(user_input)
                if shop_data:
                    shop_info = format_shop_info(shop_data)
                    # Add shop info as a separate bot message for clear display
                    st.session_state.chat_messages.append({
                        "role": "bot",
                        "content": f"Here's the information for the shop you requested:\n\n{shop_info}",
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                else:
                    st.session_state.chat_messages.append({
                        "role": "bot",
                        "content": "Sorry, I couldn’t find a matching shop. Please try specifying the town or shop name more clearly.",
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
            # Rerun to update chat display
            st.rerun()

        except httpx.ConnectError:
            st.error(f"Chatbot Error: Could not connect to Ollama server. "
                     "Please ensure Ollama is running and accessible. Re-run the app once Ollama is active.")
            st.session_state.chat_messages.append({
                "role": "bot",
                "content": "I'm unable to connect to the AI model right now. Please ensure Ollama is running and try again.",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            st.rerun()
        except Exception as e:
            st.error(f"An unexpected error occurred during chatbot interaction: {e}")
            st.session_state.chat_messages.append({
                "role": "bot",
                "content": "An error occurred while processing your request. Please try again or rephrase your question.",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            st.rerun()


# --- REMOVED: handle_image_input function is removed as image upload is no longer supported ---

# --- AI Chatbot ---
def chatbot():
    st.header("🤖 Airtel AI Assistant - Lulu")
    inject_custom_css()

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # Display chat messages in a dedicated container for better scrolling
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state.chat_messages:
        div_class = "user-message" if msg["role"] == "user" else "bot-message"
        timestamp_align = "text-align: right;" if msg["role"] == "user" else "text-align: left;"
        st.markdown(f"""
        <div style="display: flex; {"justify-content: flex-end;" if msg["role"] == "user" else "justify-content: flex-start;"}">
            <div class="chat-message {div_class}">
                {msg["content"]}
                <div class="timestamp" style="{timestamp_align}">
                    {msg["timestamp"]}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True) # Close chat container

    # Quick actions only shown at the start of a conversation
    if len(st.session_state.chat_messages) == 0:
        st.markdown("<br>", unsafe_allow_html=True) # Add some space
        st.subheader('Quick Actions')
        col1, col2 = st.columns(2)
        quick_responses = ["KYC Approval", "Float Issues","Onboarding Steps", "Follow Up on Ticket"]
        with col1:
            for response in quick_responses[:2]:
                if st.button(response, key=f"quick_action_{response}"): # Add unique key
                    handle_user_input(response)
        with col2:
            for response in quick_responses[2:]:
                if st.button(response, key=f"quick_action_{response}"): # Add unique key
                    handle_user_input(response)

    st.markdown("<br>", unsafe_allow_html=True) # Add some space before input

    # REMOVED: uploaded_image file uploader
    # uploaded_image = st.file_uploader("📎 Upload Screenshot (Optional)", type=["png", "jpg", "jpeg"])
    user_text_input = st.chat_input("Ask Lulu a question...")

    current_input = None

    if user_text_input:
        current_input = user_text_input
    # REMOVED: image input handling
    # elif uploaded_image:
    #     current_input = handle_image_input(uploaded_image)

    if current_input: # Only call handle_user_input if there's valid input
        handle_user_input(current_input)

    st.markdown("<br>", unsafe_allow_html=True) # Add some space
    if st.button("📄 Export Chat as JSON"):
        with open("chat_history.json", "w") as f:
            json.dump(st.session_state.chat_messages, f, indent=2)
        st.success("Chat history exported to chat_history.json ✅")

# Run the chatbot application
chatbot()
