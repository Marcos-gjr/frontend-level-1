import time
import requests
import streamlit as st
import os


st.set_page_config(layout="wide")

# Endpoints
BASE_URL         = os.getenv("BASE_AWS_URL")
STATUS_ENDPOINT  = f"{BASE_URL}/status"
PROCESS_ENDPOINT = f"{BASE_URL}/process"
QUERY_ENDPOINT   = f"{BASE_URL}/query"

@st.dialog("📄 Enviar PDFs", width="small")
def solicitar_pdfs():
    text = st.text_area("🔗 Cole as URLs (uma por linha)", height=120, key="dialog_pdf_urls")
    col_ok, col_cancel = st.columns(2)
    with col_ok:
        if st.button("✅ OK", key="dialog_ok"):
            urls = [u.strip() for u in text.splitlines() if u.strip()]
            if not urls:
                st.toast("Nenhuma URL válida encontrada.", icon=":material/error:")
                return
            st.toast(f"{len(urls)} URL(s) confirmada(s)!", icon=":material/check_circle:")
            try:
                r = requests.post(PROCESS_ENDPOINT, json={"urls": urls})
                r.raise_for_status()
                st.toast("Processamento iniciado!", icon=":material/rocket:")
                with st.spinner("⏳ Carregando contexto..."):
                    while True:
                        r2 = requests.get(STATUS_ENDPOINT)
                        r2.raise_for_status()
                        s = r2.json()
                        if s["status"] == "ready" and s["progress"] == 100:
                            break
                        if s["status"] == "error":
                            st.error(f"❌ Erro no servidor: {s.get('message','')}")
                            st.stop()
                        time.sleep(1)
                st.toast("✅ Contexto pronto!", icon=":material/check_circle:")
            except Exception as e:
                st.error(f"❌ Falha ao iniciar processamento: {e}")
            finally:
                st.rerun()
    with col_cancel:
        if st.button("❌ Cancelar", key="dialog_cancel"):
            st.toast("Envio cancelado.", icon=":material/cancel:")
            st.rerun()

def fetch_status():
    try:
        r = requests.get(STATUS_ENDPOINT)
        r.raise_for_status()
        return r.json()
    except:
        return {"status": "unknown", "progress": 0}

# Estado inicial
st.session_state.setdefault("messages", [
    {"role": "assistant", "content": "How can I help you?"},
])

status = fetch_status()
if status["status"] == "idle":
    solicitar_pdfs()

# HEADER COM BOTÃO PDF
col_title, col_btn = st.columns([9, 1])
with col_title:
    st.title("💬 Chatbot")
    st.caption("🚀 API de chatbot")
with col_btn:
    if st.button("📄 PDF"):
        solicitar_pdfs()

# Histórico de mensagens
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Chat
if prompt := st.chat_input("Digite aqui…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    try:
        r = requests.post(QUERY_ENDPOINT, json={"query": prompt, "k": 3})
        r.raise_for_status()
        answer = r.json().get("response", "")
        if not answer:
            raise ValueError("Resposta vazia")
    except Exception as e:
        st.error(f"❌ Erro ao obter resposta: {e}")
    else:
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.chat_message("assistant").write(answer)
