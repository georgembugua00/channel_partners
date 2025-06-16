import streamlit as st
import os
from PIL import Image
from werkzeug.utils import secure_filename
import requests
import base64
import io

# --- Configuration ---
UPLOAD_FOLDER = 'uploads'
OLLAMA_API_URL = "http://localhost:11434/api/generate" # Default Ollama API endpoint
OLLAMA_MODEL_NAME = "minicpm-v:8b" # The vision model to use
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# --- Create Upload Directory ---
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- LLM Integration Function ---
def process_image_with_llm(image_bytes, prompt_text):
    """
    Sends an image and a text prompt to the Ollama minicpm-v:8b model
    for classification and advice.
    """
    try:
        # Encode image to base64
        buffered = io.BytesIO()
        img = Image.open(io.BytesIO(image_bytes))
        img.save(buffered, format="PNG") # Save as PNG for consistent base64 encoding
        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # Define the prompt to guide the LLM's response
        full_prompt = (
            f"As an AI assistant for Airtel Sales and Distribution, analyze this image of damaged equipment. "
            f"Provide a concise 'Classification:' of the damage (e.g., Minor dent, Severe crack, Missing part, Liquid damage, etc.). "
            f"Then, provide clear, actionable 'Advice:' for an Airtel sales executive on what steps to take (e.g., 'Initiate replacement process.', 'Advise customer on repair options.', 'Document for warranty claim.', 'Escalate to technical team.', etc.). "
            f"Ensure the advice is relevant to a sales executive's role. If the image is not clear or relevant to equipment damage, state that.\n\n"
            f"User context: {prompt_text}" # Include user's additional prompt
        )

        # Construct the payload for Ollama's generate API (for vision models)
        payload = {
            "model": OLLAMA_MODEL_NAME,
            "prompt": full_prompt,
            "images": [base64_image],
            "stream": False # Set to False for single response
        }

        st.info("Sending image to Ollama for analysis...")
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=300) # Increased timeout
        response.raise_for_status() # Raise an exception for bad status codes

        result = response.json()
        generated_text = result.get('response', 'No response from model.')

        # Simple parsing of the generated text
        classification = "N/A"
        advice = "N/A"

        if "Classification:" in generated_text and "Advice:" in generated_text:
            try:
                class_start = generated_text.find("Classification:") + len("Classification:")
                advice_start = generated_text.find("Advice:")
                
                classification = generated_text[class_start:advice_start].strip()
                advice = generated_text[advice_start + len("Advice:"):].strip()
            except Exception as e:
                st.warning(f"Could not parse LLM response. Displaying raw output. Error: {e}")
                classification = "Parsing Error"
                advice = generated_text
        else:
            st.warning("LLM response did not contain expected 'Classification:' and 'Advice:' format. Displaying raw output.")
            classification = "Format Mismatch"
            advice = generated_text

        return classification, advice

    except requests.exceptions.ConnectionError:
        st.error(f"Could not connect to Ollama server at {OLLAMA_API_URL}. "
                 "Please ensure Ollama is running and the model '{OLLAMA_MODEL_NAME}' is pulled.")
        st.markdown("Run `ollama serve` in your terminal and `ollama pull minicpm-v:8b`.")
        return "Connection Error", "Please start Ollama server and pull the model."
    except requests.exceptions.Timeout:
        st.error("Ollama request timed out. The model might be taking too long to respond or is too large for your system.")
        return "Timeout Error", "Try a simpler image or check Ollama's resource usage."
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred during the Ollama API call: {e}")
        return "API Error", f"Details: {e}"
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return "Processing Error", f"Details: {e}"

# --- Streamlit UI ---
st.set_page_config(layout="centered", page_title="Airtel Equipment Damage Classifier", page_icon="📶")

# Custom CSS for a branded and amazing UI
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }

    .main {
        background-color: #090a0a; /* Light grey background */
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    .stApp {
        background-color: #000000; /* Slightly darker background for the whole app */
    }

    h1 {
        color: #E4002B; /* Airtel Red */
        text-align: center;
        font-weight: 700;
        margin-bottom: 0.5em;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }

    h2, h3 {
        color: #333333; /* Dark grey for subheaders */
        border-bottom: 2px solid #090a0a;
        padding-bottom: 0.3em;
        margin-top: 1em;
    }

    .stButton>button {
        background-color: #E4002B; /* Airtel Red button */
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.8em 1.5em;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }

    .stButton>button:hover {
        background-color: #C00021; /* Darker red on hover */
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }

    .stFileUploader {
        border: 2px dashed #B0B0B0;
        border-radius: 10px;
        padding: 1em;
        background-color: #ffffff;
    }

    .stTextInput>div>div>input {
        border-radius: 8px;
        border: 1px solid #ddd;
        padding: 0.5em;
    }

    .stTextArea>div>div>textarea {
        border-radius: 8px;
        border: 1px solid #ddd;
        padding: 0.5em;
    }

    .result-box {
        background-color: #ffffff;
        border-left: 5px solid #000000; /* Airtel Black */
        border-radius: 8px;
        padding: 1em;
        margin-top: 1.5em;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    .result-box h4 {
        color: #000000; /* Airtel Black */
        margin-top: 0;
    }

    .stAlert {
        border-radius: 8px;
    }

    .stProgress > div > div > div > div {
        background-color: #E4002B !important; /* Airtel Red progress bar */
    }

    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style="text-align: center; margin-bottom: 20px;">
        <img src="https://placehold.co/150x50/E4002B/FFFFFF?text=Airtel+Logo" alt="Airtel Logo" style="border-radius: 5px; margin-bottom: 10px;">
        <h1>Equipment Damage Classifier</h1>
        <p style="font-size: 1.1em; color: #555;">
            Empowering Airtel Sales & Distribution Executives with AI-driven damage assessment.
            Upload an image of damaged equipment to get instant classification and actionable advice.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Instructions for Ollama
st.markdown("---")
st.subheader("Ollama Setup Instructions")
st.info(
    "To use this app, ensure **Ollama** is running on your machine "
    "(visit [ollama.com](https://ollama.com/) for download and installation). "
    f"Also, make sure the `{OLLAMA_MODEL_NAME}` model is pulled by running "
    f"`ollama pull {OLLAMA_MODEL_NAME}` in your terminal."
)
st.markdown("---")


uploaded_file = st.file_uploader("Upload an image of damaged equipment", type=["png", "jpg", "jpeg", "gif"])

user_prompt_input = st.text_input(
    "Add any specific context or question for the AI (e.g., 'Is this covered by warranty?'):",
    placeholder="e.g., 'Is this damage severe enough for immediate replacement?'"
)

if uploaded_file is not None:
    # Read image bytes for processing
    image_bytes = uploaded_file.getvalue()

    # Display the uploaded image
    st.image(image_bytes, caption="Uploaded Equipment Image", use_column_width=True, channels="RGB")

    if st.button("Analyze Damage"):
        with st.spinner("Analyzing image with AI... This may take a moment."):
            classification, advice = process_image_with_llm(image_bytes, user_prompt_input)

        st.markdown("<h3 style='color:#E4002B;'>Analysis Results:</h3>", unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class="result-box">
                <h4>Classification:</h4>
                <p>{classification}</p>
            </div>
            """, unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class="result-box">
                <h4>Sales Executive Advice:</h4>
                <p>{advice}</p>
            </div>
            """, unsafe_allow_html=True
        )

else:
    st.info("Please upload an image to begin the damage classification.")

