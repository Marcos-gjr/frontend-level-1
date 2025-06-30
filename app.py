import time
import json
import requests

import streamlit as st  
from dotenv import load_dotenv
import os
load_dotenv()

# Endpoints
BASE_URL         = os.getenv("BASE_AWS_URL")
STATUS_ENDPOINT  = f"{BASE_URL}/status"
PROCESS_ENDPOINT = f"{BASE_URL}/process"
QUERY_ENDPOINT   = f"{BASE_URL}/query"

def parse_urls(text: str) -> list[str]:
    return [u.strip() for u in text.splitlines() if u.strip()]


def build_files_payload(uploaded_files) -> list[tuple]:
    return [
        ("files", (f.name, f.getvalue(), f.type))
        for f in uploaded_files
    ]


def fetch_status() -> dict:
    try:
        r = requests.get(STATUS_ENDPOINT)
        r.raise_for_status()
        return r.json()
    except:
        return {"status": "unknown", "progress": 0}


def start_processing(urls: list[str], uploaded_files, sleep=time.sleep) -> bool:
    files_payload = build_files_payload(uploaded_files)
    form_data = {"urls": json.dumps(urls)}

    r = requests.post(PROCESS_ENDPOINT, data=form_data, files=files_payload)
    r.raise_for_status()

    while True:
        s = fetch_status()
        if s["status"] == "ready" and s["progress"] == 100:
            return True
        if s["status"] == "error":
            raise RuntimeError("Erro no servidor: " + s.get("message", ""))
        sleep(1)


def query_api(query: str, k: int = 3) -> str:
    r = requests.post(QUERY_ENDPOINT, json={"query": query, "k": k})
    r.raise_for_status()

    answer = r.json().get("answer", "")
    if not answer:
        raise ValueError("Resposta vazia")
    return answer

# Envio de PDFs e URL
def main():  
    st.set_page_config(layout="wide")

    @st.dialog("📄 Enviar PDFs", width="small")
    def solicitar_pdfs():
        uploaded_files = st.file_uploader(
            "📁 Selecione arquivos PDF",
            type=["pdf"],
            accept_multiple_files=True,
            key="dialog_pdf_files"
        )
        text = st.text_area(
            "🔗 Cole as URLs (uma por linha)",
            height=120,
            key="dialog_pdf_urls"
        )

        col_ok, col_cancel = st.columns(2)
        with col_ok:
            if st.button("Enviar", key="dialog_ok"):
                urls = parse_urls(text)
                if not urls and not uploaded_files:
                    st.toast("Nenhuma URL ou arquivo válido encontrado.", icon=":material/error:")
                    return

                st.toast(f"{len(urls)} URL(s) e {len(uploaded_files)} arquivo(s) confirmados!", icon=":material/check_circle:")

                try:
                    st.toast("🚀 Processamento iniciado!", icon=":material/rocket:")
                    with st.spinner("⏳ Carregando contexto..."):
                        start_processing(urls, uploaded_files)
                    st.toast("Contexto pronto!", icon=":material/check_circle:")
                except Exception as e:
                    st.error(f"Erro ao criar contexto: {e}")
                finally:
                    st.rerun()

        with col_cancel:
            if st.button("Cancelar", key="dialog_cancel"):
                st.toast("Envio cancelado.", icon=":material/cancel:")
                st.rerun()


    # Layout
    st.session_state.setdefault("messages", [
        {"role": "assistant", "content": "Como posso lhe ajudar hoje?"},
    ])

    status = fetch_status()
    if status["status"] == "idle":
        solicitar_pdfs()

    col_title, col_btn = st.columns([9, 1])
    with col_title:
        st.title("💬 Level 1")
        st.caption("Bem-vindo ao assistente Level 1")
    with col_btn:
        if st.button("📄 PDF"):
            solicitar_pdfs()

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Digite aqui…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        try:
            answer = query_api(prompt, k=3)
        except Exception as e:
            st.error(f"Erro ao obter resposta: {e}")
        else:
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.chat_message("assistant").write(answer)


if __name__ == "__main__":
    main()