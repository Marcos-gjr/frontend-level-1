from openai import OpenAI
import streamlit as st
import requests
import time


# Template da página
st.set_page_config(layout="wide")

# Processo para carregar cada PDF
def carregar_documentacao(url: str) -> bool:
    st.toast(f"Processando: {url}", icon=":material/description:")
    time.sleep(0.5)  # simula um tempinho para processamento
    return True

# Entrada para diversos links de PDFs
@st.dialog("📄 Enviar PDFs", width="small")
def solicitar_pdfs():
    text = st.text_area(
        "🔗 Cole as URLs (uma por linha)",
        height=120,
        key="dialog_pdf_urls"
    )
    col_ok, col_cancel = st.columns(2)
    with col_ok:
        if st.button("✅ OK", key="dialog_ok"):
            # separar as linhas não vazias
            urls = [u.strip() for u in text.splitlines() if u.strip()]
            if urls:
                st.session_state.pending_pdf_urls = urls
                st.toast(f"{len(urls)} URL(s) confirmada(s)!", icon=":material/check_circle:")
                st.rerun()
            else:
                st.toast("Nenhuma URL válida encontrada.", icon=":material/error:")
    with col_cancel:
        if st.button("❌ Cancelar", key="dialog_cancel"):
            st.toast("Envio cancelado.", icon=":material/cancel:")
            st.rerun()

# Confirmação do processamento da lista
@st.dialog("⚙️ Confirmar Processamento", width="small")
def confirmar_processamento():
    urls = st.session_state.pending_pdf_urls or []
    st.write("Deseja processar estes PDFs?\n")
    for u in urls:
        st.write(f"- `{u}`")
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("✅ Processar tudo", key="confirm_ok"):
            successes = 0
            for url in urls:
                if carregar_documentacao(url):
                    successes += 1
            if successes == len(urls):
                st.toast("Todos os PDFs processados com sucesso!", icon=":material/check_circle:")
            else:
                st.toast(f"{successes}/{len(urls)} processados com sucesso.", icon=":material/warning:")
            st.session_state.pending_pdf_urls = None
            # recarrega a aplicação como um todo
            if hasattr(st, "experimental_rerun"):
                st.experimental_rerun()
            else:
                st.rerun()
    with col_no:
        if st.button("❌ Cancelar", key="confirm_cancel"):
            st.toast("Processamento cancelado.", icon=":material/cancel:")
            st.session_state.pending_pdf_urls = None
            if hasattr(st, "experimental_rerun"):
                st.experimental_rerun()
            else:
                st.rerun()

# Limpeza das chaves antigas
if "chatbot_api_key" in st.session_state:
    del st.session_state["chatbot_api_key"]

# Estado padrao
st.session_state.setdefault("messages", [
    {"role": "assistant", "content": "Como posso lhe ajudar?"},
])
st.session_state.setdefault("pending_pdf_urls", None)

# --- HEADER COM BOTÃO DO PDF ---
col_title, col_btn = st.columns([9, 1])
with col_title:
    st.title("💬 Level-1")
    st.caption("🚀 API de Suporte Level 1")
with col_btn:
    if st.button("📄 PDF"):
        solicitar_pdfs()

# Se tem links em espera, vai abrir tela de confirmação
if st.session_state.pending_pdf_urls:
    confirmar_processamento()

# Histórico de mensagens
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Chat padrão
if prompt := st.chat_input("Digite aqui…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    resp = requests.post(
        "http://127.0.0.1:8001/query",
        json={"query": prompt, "k": 3},
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    resp.raise_for_status()
    answer = resp.json().get("response", "erro ao renderizar")
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.chat_message("assistant").write(answer)
