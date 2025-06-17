import streamlit as st
import json
import datetime
import requests # Used for making HTTP requests to the AI Navigator API
import re
import os # For potentially loading API key from environment variables

# --- Configuration for AI Navigator Anaconda LLM API ---
# IMPORTANT: Replace with the actual URL and API Key from AI Navigator Anaconda
AI_NAVIGATOR_API_URL = "http://localhost:8000/generate" # Example: Adjust based on your AI Navigator setup
AI_NAVIGATOR_API_KEY = os.getenv("AI_NAVIGATOR_API_KEY", "your_default_or_placeholder_key") # Load from environment or provide securely

# --- Model & Memory Setup (No direct LLM instantiation here, as we're calling a custom API) ---
@st.cache_resource
def init_llm_and_memory():
    # In this setup, we don't directly instantiate LangChain's LLM here.
    # Instead, the LLM interaction happens via HTTP requests in handle_user_input.
    # We still need memory for conversation history.
    st.info("Initializing conversation memory for AI Navigator integration.")
    return None, None # No direct llm or embedder objects returned in this custom API setup

# Use the function to initialize memory (llm and embedder will be None)
_, _ = init_llm_and_memory() # Assign to dummy variables if not used directly

# Initialize session state for chat messages if not already present
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
# Initialize memory and chat_chain outside of the cached function
if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
if "chat_chain" not in st.session_state:
    # We won't use LangChain's ConversationChain directly if we're making raw API calls.
    # The prompt formatting and history management will be handled manually in handle_user_input.
    st.session_state.chat_chain = None # Set to None or remove if not used at all


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
            border-bottom-left-radius: 44px; /* Tail effect */
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
    match = re.search(r"<think>(.*?)</think>", response_text, re.DOTALL)
    if match:
        thought = match.group(1).strip()
        cleaned_response = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL).strip()
        return thought, cleaned_response
    return None, response_text

# Load shop data from JSON file (ensure this path is correct on your system)
try:
    with open("/Users/danielwanganga/Documents/ChatBot/shop_location.json", "r") as f:
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
    plus_code = shop_data.get("Plus Code", "")
    lat = shop_data.get("Latitude")
    lon = shop_data.get("Longitude")
    # Corrected Google Maps link format
    maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}" if lat and lon else ""
    return f"**{name}**\n📍 {location}\n🕒 {shop_data.get('Business Hours', '')}\n🌍 [View on Maps]({maps_link})"

def is_shop_query(user_input):
    keywords = ["shop", "location", "nearest shop", "where can I find", "shop near me"]
    return any(k in user_input.lower() for k in keywords)

# --- Updated handle_user_input to use custom API calls ---
def handle_user_input(user_input):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Add user message to history
    st.session_state.chat_messages.append({
        "role": "user",
        "content": user_input,
        "timestamp": timestamp
    })

    with st.spinner("Lulu is thinking..."):
        full_prompt = (
            "You are Lulu, an intelligent AI assistant working at Airtel Kenya. "
            "Your job is to support Sales Executives who manage over 200 on-the-ground agents. "
            "Help them with operations, float requests, KYC issues, training updates, and urgent tickets. "
            "Always respond professionally, concisely, and with context relevant to Airtel's field operations.\n\n"
            f"Current conversation:\n{st.session_state.memory.buffer_as_str}\n"
            f"Human: {user_input}\n"
            "Assistant:"
        )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {AI_NAVIGATOR_API_KEY}" # Only if API Key is required
        }
        payload = {
            "prompt": full_prompt,
            "max_new_tokens": 200, # Adjust as needed for your model and desired response length
            "temperature": 0.7,
            # Add other parameters specific to AI Navigator Anaconda's API if available (e.g., top_p, do_sample)
        }

        try:
            response = requests.post(AI_NAVIGATOR_API_URL, headers=headers, json=payload, timeout=120) # Add timeout
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            api_response_data = response.json()

            # Assuming the response structure contains the generated text in a key like 'generated_text'
            # You will need to adjust this based on the actual API response from AI Navigator Anaconda
            generated_text = api_response_data.get("generated_text", "No text generated.")

            # Update LangChain memory with the new interaction
            st.session_state.memory.save_context({"input": user_input}, {"output": generated_text})

            # Parse thoughts if any (assuming AI Navigator might also output thoughts)
            thought, cleaned_response = parse_thoughts(generated_text)
            if thought:
                with st.expander("🤖 Internal reasoning"):
                    st.markdown(thought)
                response_content = cleaned_response
            else:
                response_content = generated_text

            # Add bot message to history
            st.session_state.chat_messages.append({
                "role": "bot",
                "content": response_content,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            # Special handling for shop queries after LLM response
            if is_shop_query(user_input):
                shop_data = find_shop_by_keyword(user_input)
                if shop_data:
                    shop_info = format_shop_info(shop_data)
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
            st.rerun()

        except requests.exceptions.ConnectionError as e:
            st.error(f"Connection Error: Could not connect to AI Navigator Anaconda server at {AI_NAVIGATOR_API_URL}. "
                     "Please ensure the server is running and accessible.")
            st.session_state.chat_messages.append({
                "role": "bot",
                "content": "I'm unable to connect to the AI model right now. Please ensure AI Navigator Anaconda server is running and accessible.",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            st.rerun()
        except requests.exceptions.HTTPError as e:
            st.error(f"HTTP Error: An error occurred with the API request: {e}. Response: {e.response.text}")
            st.session_state.chat_messages.append({
                "role": "bot",
                "content": f"The AI model returned an error: {e.response.status_code}. Please check the server logs.",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            st.rerun()
        except requests.exceptions.Timeout:
            st.error(f"Timeout Error: The request to AI Navigator Anaconda server timed out after 120 seconds.")
            st.session_state.chat_messages.append({
                "role": "bot",
                "content": "The AI model is taking too long to respond. Please try again or rephrase your question.",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            st.rerun()
        except json.JSONDecodeError:
            st.error("API Response Error: Could not decode JSON from AI Navigator Anaconda server response. "
                     "Check server logs for unexpected output format.")
            st.session_state.chat_messages.append({
                "role": "bot",
                "content": "Received an unreadable response from the AI model. Please check server configuration.",
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


# --- AI Chatbot ---
def chatbot():
    st.header("🤖 Airtel AI Assistant - Lulu")
    inject_custom_css()

    # Chat messages are managed here.
    # st.session_state.chat_messages is initialized in init_llm_and_memory,
    # but it's more conventional to initialize it directly in chatbot()
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

    user_text_input = st.chat_input("Ask Lulu a question...")

    current_input = None

    if user_text_input:
        current_input = user_text_input

    if current_input: # Only call handle_user_input if there's valid input
        handle_user_input(current_input)

    st.markdown("<br>", unsafe_allow_html=True) # Add some space
    if st.button("📄 Export Chat as JSON"):
        with open("chat_history.json", "w") as f:
            json.dump(st.session_state.chat_messages, f, indent=2)
        st.success("Chat history exported to chat_history.json ✅")

# Run the chatbot application
chatbot()
