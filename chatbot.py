import streamlit as st
from langchain_ollama import ChatOllama
from langchain.vectorstores import FAISS
from langchain.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

from PyPDF2 import PdfReader
import pandas as pd

# --- Initialize LLM + Embeddings ---
llm = ChatOllama(model="llama3.2", temperature=0.4)
embedder = OllamaEmbeddings(model="mxbai-embed-large")

# --- Setup Streamlit session state ---
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
if "chat_chain" not in st.session_state:
    st.session_state.chat_chain = None

# --- File Upload ---
st.sidebar.title("📁 Upload Knowledge Files")
uploaded_file = st.sidebar.file_uploader("Upload PDF, CSV, or XLSX", type=["pdf", "csv", "xlsx"])

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

    elif file.name.endswith(".xlsx"):
        df = pd.read_excel(file)
        raw_text = df.to_string()
        docs = [Document(page_content=raw_text)]

    # Split and embed
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    splits = splitter.split_documents(docs)
    st.session_state.vector_store = FAISS.from_documents(splits, embedder)

    # RAG chain with memory
    st.session_state.chat_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=st.session_state.vector_store.as_retriever(),
        memory=st.session_state.memory,
        return_source_documents=True,
        output_key = "answer"
    )
    st.sidebar.success("✅ File indexed and memory enabled!")

if uploaded_file:
    process_file(uploaded_file)

# --- Chat UI ---
st.title("🤖 Airtel Kenya Sales Executive Assistant")

prompt = st.chat_input("Ask a question about Airtel operations, support, or float...")

if "messages" not in st.session_state:
    st.session_state.messages = []

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # RAG + Memory response
    if st.session_state.chat_chain:
        result = st.session_state.chat_chain.invoke({"question": prompt})
        response = result['answer']
    else:
        response = llm.invoke([{"role": "user", "content": prompt}]).content

    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

# --- Optional Summarize Button ---
if st.button("🧠 Summarize Chat"):
    history_text = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state.messages])
    summary_prompt = f"""Summarize the following chat history in bullet points for a Sales Executive at Airtel Kenya:\n\n{history_text}"""
    summary = llm.invoke([{"role": "user", "content": summary_prompt}]).content

    st.markdown("### 📝 Conversation Summary")
    st.success(summary)
