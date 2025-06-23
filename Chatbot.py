from openai import OpenAI
import streamlit as st
import requests
import os

OPENAI_API_KEY = os.getenv("OPENAI_API")


st.set_page_config(layout="wide")
if "chatbot_api_key" in st.session_state:
    del st.session_state["chatbot_api_key"]


openai_api_key = OPENAI_API_KEY

st.title("💬 Level-1")
st.caption("🚀 API de Suporte Level 1")


if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Como posso lhe ajudar?"},
        {"role": "user", "content": "teste"},
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])


if prompt := st.chat_input(placeholder="Digite aqui…"):


    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)


    url = "http://127.0.0.1:8001/query"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    payload = {
        "query": prompt,
        "k": 3
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()  
    msg = response.json().get("response","erro ao renderizar")

    print(msg)


    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
