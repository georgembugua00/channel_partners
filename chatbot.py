import datetime
import re
import json
from langchain_ollama import ChatOllama
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.embeddings import OllamaEmbeddings
from ollama import Client

# --- Model & Memory Setup ---
def init_llm_and_memory():
    llm = ChatOllama(model="llama3.2", temperature=0.4)
    embedder = OllamaEmbeddings(model="nomic-embed-text")
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    prompt_template = PromptTemplate(
        input_variables=["chat_history", "input"],
        template="""You are Lulu, an intelligent AI assistant working at Airtel Kenya. \
Your job is to support Sales Executives who manage over 200 on-the-ground agents. \
Help them with operations, float requests, KYC issues, training updates, and urgent tickets. \
Always respond professionally, concisely, and with context relevant to Airtel's field operations.

Current conversation:
{chat_history}
Human: {input}
Assistant:"""
    )

    chat_chain = ConversationChain(llm=llm, memory=memory, prompt=prompt_template)
    return chat_chain, memory, embedder

# --- Shop Utilities ---
def load_shop_locations(path="shop_location.json"):
    with open(path, "r") as f:
        return json.load(f)

def find_shop_by_keyword(query, shop_locations):
    for shop_name, shop_data in shop_locations.items():
        if shop_name.lower() in query.lower():
            return shop_data
    return None

def format_shop_info(shop_data):
    name = shop_data.get("SHOP NAME", "N/A")
    location = shop_data.get("PHYSICAL LOCATION", "N/A")
    lat, lon = shop_data.get("Latitude"), shop_data.get("Longitude")
    maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}" if lat and lon else ""
    return f"**{name}**\n📍 {location}\n🕒 {shop_data.get('Business Hours', '')}\n🌍 [View on Maps]({maps_link})"

def is_shop_query(text):
    keywords = ["shop", "location", "nearest shop", "where can I find", "shop near me"]
    return any(k in text.lower() for k in keywords)

# --- Thought Extraction ---
def parse_thoughts(response_text):
    match = re.search(r"<think>(.*?)</think>", response_text, re.DOTALL)
    if match:
        thought = match.group(1).strip()
        cleaned_response = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL).strip()
        return thought, cleaned_response
    return None, response_text

# --- Input Handler ---
def handle_user_input(user_input, chat_chain, shop_locations, message_history, use_vector_store=False):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message_history.append({"role": "user", "content": user_input, "timestamp": timestamp})

    input_key = "question" if use_vector_store else "input"
    result = chat_chain.invoke({input_key: user_input})

    # Extract response
    response = result.get("answer") or result.get("response") or str(result)
    thought, cleaned_response = parse_thoughts(response)
    if thought:
        response = cleaned_response

    message_history.append({"role": "bot", "content": response, "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

    # Add shop info if detected
    if is_shop_query(user_input):
        shop_data = find_shop_by_keyword(user_input, shop_locations)
        if shop_data:
            shop_info = format_shop_info(shop_data)
            message_history.append({"role": "bot", "content": f"Here's the information for the shop you requested:\n\n{shop_info}", "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        else:
            message_history.append({"role": "bot", "content": "Sorry, I couldn’t find a matching shop. Please try specifying the town or shop name more clearly.", "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

    return message_history, thought
