#!/usr/bin/env python3
"""Browser-based chat interface for the CS major handbook RAG system."""

from pathlib import Path

import streamlit as st
from langchain_ollama import OllamaEmbeddings, OllamaLLM

import run_txt


APP_DIR = Path(__file__).resolve().parent
HANDBOOK_PATH = APP_DIR / "major_handbook_pdfs" / "CS_MajorHandbook.pdf"
VECTOR_STORE_PATH = APP_DIR / "data_txt" / "cs_handbook_vector_store"


st.set_page_config(
    page_title="CS Handbook Chatbot",
    page_icon="📚",
    layout="centered",
)

st.markdown(
    """
    <style>
    .block-container { max-width: 900px; padding-top: 2rem; padding-bottom: 5rem; }
    [data-testid="stChatMessage"] { border-radius: 14px; }
    .source-label { color: #526174; font-size: 0.9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner=False)
def load_backend():
    embeddings = OllamaEmbeddings(
        model=run_txt.EMBED_MODEL,
        base_url=run_txt.OLLAMA_URL,
    )
    db = run_txt.load_and_index(
        embeddings,
        data_dir=str(HANDBOOK_PATH),
        vector_store=str(VECTOR_STORE_PATH),
    )
    llm = OllamaLLM(
        model=run_txt.LLM_MODEL,
        base_url=run_txt.OLLAMA_URL,
        temperature=run_txt.TEMPERATURE,
    )
    return db, llm


def show_sources(message):
    sources = message.get("sources", [])
    if message.get("used_fallback"):
        st.caption("Không tìm thấy đoạn handbook đủ liên quan để làm căn cứ trả lời.")
        return
    if not sources:
        return

    with st.expander(f"Nguồn tham khảo ({len(sources)})"):
        for source in sources:
            page = source.get("page")
            page_text = f" · trang {page}" if page is not None else ""
            st.markdown(
                f"<span class='source-label'><b>{source['source']}</b>"
                f"{page_text} · độ phù hợp {source['score']:.2f}</span>",
                unsafe_allow_html=True,
            )


st.title("📚 CS Handbook Chatbot")
st.caption(
    "Tra cứu sổ tay ngành Computer Science. Mỗi câu trả lời hiển thị trang nguồn "
    "để bạn kiểm tra lại thông tin."
)

with st.sidebar:
    st.subheader("Tài liệu đang dùng")
    st.markdown("**CS Major Handbook**")
    st.caption("Câu trả lời được tạo từ nội dung sổ tay đã chọn.")
    st.markdown("**Embedding:** `nomic-embed-text`")
    st.markdown(f"**Mô hình trả lời:** `{run_txt.LLM_MODEL}`")
    st.divider()
    if st.button("Xóa cuộc trò chuyện", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

if not HANDBOOK_PATH.is_file():
    st.error(f"Không tìm thấy handbook: {HANDBOOK_PATH.name}")
    st.stop()

try:
    with st.spinner("Đang kết nối Ollama và nạp handbook..."):
        db, llm = load_backend()
except Exception as error:
    st.error(
        "Không thể khởi tạo chatbot. Hãy kiểm tra Ollama và địa chỉ `OLLAMA_URL`."
    )
    with st.expander("Chi tiết lỗi"):
        st.code(str(error))
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            show_sources(message)

question = st.chat_input(
    "Nhập câu hỏi về yêu cầu ngành, môn học hoặc chuẩn đầu ra..."
)

if question:
    user_message = {"role": "user", "content": question}
    st.session_state.messages.append(user_message)
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm trong handbook..."):
            try:
                result = run_txt.ask(question, db, llm)
            except Exception as error:
                st.error("Có lỗi khi tìm kiếm hoặc tạo câu trả lời.")
                with st.expander("Chi tiết lỗi"):
                    st.code(str(error))
                st.stop()

        assistant_message = {
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"][:3],
            "used_fallback": result["used_fallback"],
        }
        st.session_state.messages.append(assistant_message)
        st.markdown(assistant_message["content"])
        show_sources(assistant_message)
