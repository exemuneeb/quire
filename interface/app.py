import os
import sys
import re
import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

# ─── Path setup ──────────────────────────────────────────────────────────────
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in [ROOT_DIR, os.getcwd()]:
    if p not in sys.path:
        sys.path.insert(0, p)

import config
from config import (
    EMBEDDING_MODELS, GROQ_MODELS, DEFAULT_GROQ_MODEL,
    DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP, DEFAULT_TOP_K,
    DEFAULT_DISTANCE_THRESHOLD, DEFAULT_EMBEDDING_MODEL_KEY, APP_NAME, APP_TAGLINE,
)
from intake.source_manager import SourceManager
from vectorize.manager import EmbeddingManager
from store.vector_store import VectorStore
from engine.retriever import Retriever
from engine.llm import GroqClient
from telemetry.performance_monitor import PerformanceMonitor
from interface.styles import CUSTOM_CSS


# ─── Small helpers ───────────────────────────────────────────────────────────
def clean_source_filename(fname: str) -> str:
    if not fname:
        return ""
    parts = fname.split("_", 1)
    if len(parts) == 2 and len(parts[0]) == 8:
        return parts[1]
    return fname


def clean_answer_html(content: str) -> str:
    if not content:
        return ""
    text = re.sub(r"\[Source:\s*[^\]]+\]", "", content, flags=re.IGNORECASE)
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.*?)\*", r"<em>\1</em>", text)
    return text.replace("\n", "<br>").strip()


def fmt_size(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.0f} KB"
    return f"{num_bytes / (1024 * 1024):.1f} MB"


def get_active_sources():
    return st.session_state.source_manager.get_active_sources()


NAV_ITEMS = ["Ask", "Library", "Connect", "Insights", "Tuning"]
SUGGESTED_PROMPTS = ["How does retrieval work?", "What is a vector embedding?", "Explain the grounding score", "Chunking best practices"]
BAR_COLORS = ["#b4501f", "#3f6b52", "#b48a1f", "#8a6d5c", "#a49a8b"]

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(page_title=f"{APP_NAME} — {APP_TAGLINE}", layout="centered", initial_sidebar_state="collapsed")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ─── Session state ────────────────────────────────────────────────────────────
defaults = {
    "chat_history": [],
    "llm_model": DEFAULT_GROQ_MODEL,
    "emb_model_key": DEFAULT_EMBEDDING_MODEL_KEY,
    "top_k": DEFAULT_TOP_K,
    "distance_threshold": DEFAULT_DISTANCE_THRESHOLD,
    "search_type": "Similarity Search",
    "chunk_size": DEFAULT_CHUNK_SIZE,
    "chunk_overlap": DEFAULT_CHUNK_OVERLAP,
    "active_page": "Ask",
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

if "source_manager" not in st.session_state:
    st.session_state.source_manager = SourceManager()
if "perf_monitor" not in st.session_state:
    st.session_state.perf_monitor = PerformanceMonitor()

groq_key = os.getenv("GROQ_API_KEY", "")


@st.cache_resource(show_spinner=False)
def get_engine(emb_key: str):
    embedder = EmbeddingManager.get_embedder(emb_key)
    store = VectorStore(embedder=embedder)
    return embedder, store


try:
    embedder_inst, vector_store = get_engine(st.session_state.emb_model_key)
    retriever = Retriever(vector_store)
except Exception:
    vector_store, retriever = None, None


# ─── Top bar: wordmark + nav pills (replaces the old sidebar dashboard) ─────
top_cols = st.columns([2.2, 1, 1, 1, 1, 1])
with top_cols[0]:
    st.markdown(
        f'<div class="quire-wordmark">Qu<span>i</span>re</div>'
        f'<div class="quire-tagline">{APP_TAGLINE}</div>',
        unsafe_allow_html=True,
    )
for i, label in enumerate(NAV_ITEMS):
    with top_cols[i + 1]:
        is_active = st.session_state.active_page == label
        st.markdown(f'<div class="nav-pill{" nav-pill-active" if is_active else ""}" style="margin-top:10px;">', unsafe_allow_html=True)
        if st.button(label, key=f"nav_{label}", use_container_width=True):
            st.session_state.active_page = label
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)
active_page = st.session_state.active_page


# ═══════════════════════════════════ ASK ═════════════════════════════════════
if active_page == "Ask":
    if not st.session_state.chat_history:
        st.markdown(
            f"""<div class="ask-hero">
                <div class="ask-hero-title">What do you want to know?</div>
                <div class="ask-hero-sub">Quire reads only what you've connected — every answer is traced back to a passage, or it tells you it can't find one.</div>
            </div>""",
            unsafe_allow_html=True,
        )
        chip_cols = st.columns(4)
        for i, p_text in enumerate(SUGGESTED_PROMPTS):
            with chip_cols[i]:
                st.markdown('<div class="chip-btn">', unsafe_allow_html=True)
                if st.button(p_text, key=f"chip_{i}"):
                    st.session_state._pending_query = p_text
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    else:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                now_str = datetime.datetime.now().strftime("%I:%M %p").lstrip("0")
                st.markdown(
                    f'<div class="msg-user"><div class="msg-user-bubble">{message["content"]}</div></div>',
                    unsafe_allow_html=True,
                )
            else:
                sources_html = ""
                if message.get("sources"):
                    seen, unique_sources = set(), []
                    for src in message["sources"]:
                        name = clean_source_filename(src.get("filename", ""))
                        if name and name not in seen:
                            seen.add(name)
                            unique_sources.append(src)
                    if unique_sources:
                        sources_html = '<div class="msg-sources">'
                        for src in unique_sources:
                            name = clean_source_filename(src.get("filename", ""))
                            page = src.get("page", 1)
                            page_str = f" · p.{page}" if isinstance(page, int) and page > 0 else ""
                            sources_html += f'<span class="src-tag">{name}{page_str}</span>'
                        sources_html += "</div>"

                meta_html = ""
                if message.get("metrics"):
                    m = message["metrics"]
                    gci = int(m.get("grounding_confidence_index", 0) * 100)
                    latency = m.get("total_latency_ms", 0)
                    meta_html = f'<div class="msg-meta"><span class="grounded">{gci}% grounded</span><span>{latency:.0f}ms</span></div>'

                st.markdown(
                    f'<div class="msg-assistant"><div class="msg-label">Quire</div>'
                    f'<div class="msg-body">{clean_answer_html(message["content"])}</div>'
                    f'{meta_html}{sources_html}</div>',
                    unsafe_allow_html=True,
                )

    query = st.chat_input("Ask a question about what you've connected...", key="main_chat_input")
    if getattr(st.session_state, "_pending_query", None):
        query = st.session_state._pending_query
        del st.session_state._pending_query

    if query:
        st.session_state.chat_history.append({"role": "user", "content": query})
        active_sources_now = get_active_sources()

        if not active_sources_now:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "Nothing's connected yet — add a document or a link on the Connect page first.",
                "sources": [], "metrics": {},
            })
            st.rerun()
        elif retriever is None:
            st.session_state.chat_history.append({
                "role": "assistant", "content": "The retrieval engine failed to start up.",
                "sources": [], "metrics": {},
            })
            st.rerun()
        else:
            with st.spinner("Reading through your sources..."):
                retrieved_items, formatted_context, retrieval_ms, comp_stats = retriever.retrieve(
                    query, top_k=st.session_state.top_k, search_type=st.session_state.search_type,
                    distance_threshold=st.session_state.distance_threshold,
                )
            with st.spinner("Composing an answer..."):
                try:
                    answer_text, gen_ms = GroqClient.generate(
                        model_name=st.session_state.llm_model, query=query,
                        context=formatted_context, api_key=groq_key,
                    )
                    log_entry = st.session_state.perf_monitor.log_query_event(
                        query=query, response=answer_text, retrieved_chunks=retrieved_items,
                        retrieval_time_ms=retrieval_ms, gen_time_ms=gen_ms,
                        embedding_model=st.session_state.emb_model_key, llm_model=st.session_state.llm_model,
                        active_source_count=len(active_sources_now), compression_stats=comp_stats,
                    )
                    st.session_state.chat_history.append({
                        "role": "assistant", "content": answer_text,
                        "sources": retrieved_items, "metrics": log_entry,
                    })
                except Exception as e:
                    st.session_state.chat_history.append({
                        "role": "assistant", "content": f"Something went wrong: {e}", "sources": [], "metrics": {},
                    })
            st.rerun()

    st.markdown(f'<div class="quire-footer">{len(get_active_sources())} source(s) connected · Groq + ChromaDB</div>', unsafe_allow_html=True)


# ═══════════════════════════════════ LIBRARY ═════════════════════════════════
elif active_page == "Library":
    st.markdown('<div class="page-kicker">Registry</div><div class="page-heading">Library</div><div class="page-sub">Every source currently indexed, and what it cost to store.</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

    active_sources_now = get_active_sources()
    if active_sources_now:
        df = pd.DataFrame(active_sources_now)[["source_id", "filename", "total_chunks", "file_size", "chunk_size", "chunk_overlap"]]
        df.columns = ["ID", "Name", "Chunks", "Size", "Chunk Size", "Overlap"]
        df["Size"] = df["Size"].apply(fmt_size)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
        col_sel, col_btn = st.columns([3, 1])
        with col_sel:
            target_id = st.selectbox(
                "Remove a source", options=[s["source_id"] for s in active_sources_now],
                format_func=lambda x: next(s["filename"] for s in active_sources_now if s["source_id"] == x),
                label_visibility="collapsed",
            )
        with col_btn:
            if st.button("Remove", use_container_width=True):
                removed = st.session_state.source_manager.remove_source(target_id)
                if removed and vector_store:
                    vector_store.delete_source(target_id)
                st.rerun()

        if st.button("Clear entire library"):
            st.session_state.source_manager.clear_all()
            if vector_store:
                vector_store.reset()
            st.rerun()
    else:
        st.markdown('<div class="paper-block">Nothing indexed yet. Head to <strong>Connect</strong> to add a source.</div>', unsafe_allow_html=True)


# ═══════════════════════════════════ CONNECT ═════════════════════════════════
elif active_page == "Connect":
    st.markdown('<div class="page-kicker">Ingestion</div><div class="page-heading">Connect a source</div><div class="page-sub">Upload files or point at a web page — Quire reads, chunks, and indexes it automatically.</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="paper-block"><div class="section-label">Upload files</div>', unsafe_allow_html=True)
        uploaded_files = st.file_uploader("Files", type=["pdf", "txt", "docx"], accept_multiple_files=True, label_visibility="collapsed")
        if st.button("Process & index", use_container_width=True, key="process_files_btn"):
            if uploaded_files:
                for file in uploaded_files:
                    with st.spinner(f"Reading {file.name}..."):
                        file_bytes = file.read()
                        _, chunks = st.session_state.source_manager.add_file(
                            file_name=file.name, file_bytes=file_bytes,
                            chunk_size=st.session_state.chunk_size, chunk_overlap=st.session_state.chunk_overlap,
                        )
                        if vector_store:
                            vector_store.add_documents(chunks)
                    st.success(f"Indexed {file.name}")
                st.rerun()
            else:
                st.info("Choose one or more files first.")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="paper-block"><div class="section-label">Index a web page</div>', unsafe_allow_html=True)
        web_url = st.text_input("URL", placeholder="https://example.com/article", label_visibility="collapsed")
        if st.button("Fetch & index", use_container_width=True, key="index_url_btn"):
            if web_url.strip():
                with st.spinner("Fetching page..."):
                    try:
                        _, chunks = st.session_state.source_manager.add_url(
                            url=web_url, chunk_size=st.session_state.chunk_size, chunk_overlap=st.session_state.chunk_overlap,
                        )
                        if vector_store:
                            vector_store.add_documents(chunks)
                        st.success("Indexed.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not fetch that page: {e}")
            else:
                st.info("Paste a URL first.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="page-kicker" style="margin-top:10px;">Connected</div>', unsafe_allow_html=True)

    active_sources_now = get_active_sources()
    if active_sources_now:
        rows_html = '<div class="paper-block">'
        for src in active_sources_now:
            fname = src.get("filename", "Unknown")
            fsize = fmt_size(src.get("file_size", 0))
            chunks = src.get("total_chunks", 0)
            added_at = src.get("added_at", "just now")
            rows_html += (
                f'<div class="source-row"><div><div class="source-name">{fname}</div>'
                f'<div class="source-meta">{fsize} · {chunks} chunks · added {added_at}</div></div></div>'
            )
        rows_html += "</div>"
        st.markdown(rows_html, unsafe_allow_html=True)
    else:
        st.markdown('<div class="paper-block" style="color:var(--ink-faint);">Nothing connected yet.</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="page-kicker" style="margin-top:6px;">How ingestion works</div>', unsafe_allow_html=True)
    for title, desc in [
        ("Multi-format extraction", "Native parsing for PDF (with OCR fallback for scans), DOCX, TXT, and live web pages."),
        ("Recursive chunking", "A pure-Python sliding-window splitter with configurable size and overlap."),
        ("Local vector index", "Chunks are embedded locally and stored in ChromaDB, with true delete-on-remove per source."),
    ]:
        st.markdown(
            f'<div class="paper-block" style="padding:14px 18px;"><div style="font-weight:700;font-size:0.86rem;margin-bottom:3px;">{title}</div>'
            f'<div style="font-size:0.80rem;color:var(--ink-soft);line-height:1.45;">{desc}</div></div>',
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════ INSIGHTS ════════════════════════════════
elif active_page == "Insights":
    st.markdown('<div class="page-kicker">Telemetry</div><div class="page-heading">Insights</div><div class="page-sub">How Quire is performing across every question asked so far.</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

    logs = st.session_state.perf_monitor.load_logs()
    total_queries = len(logs)

    if logs:
        df_logs = pd.DataFrame(logs)
        avg_latency_s = df_logs["total_latency_ms"].mean() / 1000
        avg_gci = df_logs["grounding_confidence_index"].mean() * 100
        high_risk = len(df_logs[df_logs["hallucination_risk"] == "HIGH_RISK"])
        hallucination_rate = (high_risk / total_queries * 100) if total_queries else 0

        st.markdown(
            f"""<div class="stat-strip">
                <div class="stat-cell"><div class="stat-num">{total_queries}</div><div class="stat-lbl">Questions asked</div></div>
                <div class="stat-cell"><div class="stat-num">{avg_latency_s:.2f}s</div><div class="stat-lbl">Avg. response</div></div>
                <div class="stat-cell"><div class="stat-num">{avg_gci:.0f}%</div><div class="stat-lbl">Avg. grounding</div></div>
                <div class="stat-cell"><div class="stat-num">{hallucination_rate:.0f}%</div><div class="stat-lbl">High-risk answers</div></div>
            </div>""",
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="section-label">Latency by stage</div>', unsafe_allow_html=True)
            fig_lat = px.bar(df_logs, x="query_id", y=["retrieval_latency_ms", "generation_latency_ms"],
                              barmode="stack", color_discrete_sequence=["#b4501f", "#3f6b52"])
            fig_lat.update_layout(paper_bgcolor="#faf7f1", plot_bgcolor="#ffffff", font_color="#635c51",
                                   legend_title_text="", margin=dict(t=10, l=10, r=10, b=10))
            st.plotly_chart(fig_lat, use_container_width=True)
        with c2:
            st.markdown('<div class="section-label">Grounding over time</div>', unsafe_allow_html=True)
            fig_gci = px.line(df_logs, x="query_id", y=["grounding_confidence_index", "lexical_overlap_ratio"],
                               markers=True, color_discrete_sequence=["#b4501f", "#b48a1f"])
            fig_gci.update_layout(paper_bgcolor="#faf7f1", plot_bgcolor="#ffffff", font_color="#635c51",
                                   legend_title_text="", margin=dict(t=10, l=10, r=10, b=10))
            st.plotly_chart(fig_gci, use_container_width=True)

        active_sources_now = get_active_sources()
        if active_sources_now:
            st.markdown('<div class="section-label" style="margin-top:6px;">Where chunks come from</div>', unsafe_allow_html=True)
            total_chunks = sum(s.get("total_chunks", 1) for s in active_sources_now) or 1
            bars_html = '<div class="paper-block">'
            for i, src in enumerate(active_sources_now[:6]):
                fname = clean_source_filename(src.get("filename", "Unknown"))
                chunks = src.get("total_chunks", 0)
                pct = round(chunks / total_chunks * 100)
                color = BAR_COLORS[i % len(BAR_COLORS)]
                bars_html += (
                    f'<div class="bar-row"><div class="bar-label" title="{fname}">{fname}</div>'
                    f'<div class="bar-track"><div class="bar-fill" style="width:{pct}%;background:{color};"></div></div>'
                    f'<div class="bar-pct">{pct}%</div></div>'
                )
            bars_html += "</div>"
            st.markdown(bars_html, unsafe_allow_html=True)

        if st.button("Clear telemetry log"):
            st.session_state.perf_monitor.clear_logs()
            st.rerun()
    else:
        st.markdown('<div class="paper-block">Nothing logged yet — ask a question on the Ask page.</div>', unsafe_allow_html=True)

    st.markdown('<div class="page-kicker" style="margin-top:10px;">System</div>', unsafe_allow_html=True)
    vdb_status = "Healthy" if vector_store else "Offline"
    llm_status = "Healthy" if groq_key else "No API key"
    st.markdown(
        f"""<div class="paper-block">
            <div class="status-row"><span><span class="status-dot{'' if vector_store else ' down'}"></span>Vector index (ChromaDB)</span><span>{vdb_status}</span></div>
            <div class="status-row"><span><span class="status-dot{'' if groq_key else ' down'}"></span>LLM inference (Groq)</span><span>{llm_status}</span></div>
            <div class="status-row"><span><span class="status-dot"></span>Local embeddings (HuggingFace)</span><span>Healthy</span></div>
        </div>""",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════ TUNING ═══════════════════════════════════
elif active_page == "Tuning":
    st.markdown('<div class="page-kicker">Configuration</div><div class="page-heading">Tuning</div><div class="page-sub">Adjust the model and retrieval parameters for this session.</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

    st.markdown('<div class="paper-block">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Inference model (Groq)</div>', unsafe_allow_html=True)
    st.session_state.llm_model = st.selectbox("LLM", GROQ_MODELS, index=GROQ_MODELS.index(st.session_state.llm_model), label_visibility="collapsed")

    st.markdown('<div class="section-label" style="margin-top:16px;">Embedding model</div>', unsafe_allow_html=True)
    emb_keys = list(EMBEDDING_MODELS.keys())
    new_emb_key = st.selectbox("Embedding", emb_keys, index=emb_keys.index(st.session_state.emb_model_key), label_visibility="collapsed")
    if new_emb_key != st.session_state.emb_model_key:
        st.session_state.emb_model_key = new_emb_key
        st.cache_resource.clear()
        st.rerun()

    st.markdown('<div class="section-label" style="margin-top:16px;">Search strategy</div>', unsafe_allow_html=True)
    st.session_state.search_type = st.selectbox(
        "Search", ["Similarity Search", "Maximal Marginal Relevance (MMR)"],
        index=0 if st.session_state.search_type == "Similarity Search" else 1, label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="paper-block">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Retrieval depth (top-k)</div>', unsafe_allow_html=True)
    st.session_state.top_k = st.slider("TopK", 1, 12, st.session_state.top_k, label_visibility="collapsed")

    st.markdown('<div class="section-label" style="margin-top:16px;">Max cosine distance</div>', unsafe_allow_html=True)
    st.session_state.distance_threshold = st.slider("Dist", 0.1, 2.0, st.session_state.distance_threshold, step=0.05, label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="paper-block">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Chunk size</div>', unsafe_allow_html=True)
    st.session_state.chunk_size = st.slider("ChunkSize", 100, 2000, st.session_state.chunk_size, step=50, label_visibility="collapsed")

    st.markdown('<div class="section-label" style="margin-top:16px;">Chunk overlap</div>', unsafe_allow_html=True)
    st.session_state.chunk_overlap = st.slider("ChunkOverlap", 0, 400, st.session_state.chunk_overlap, step=10, label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div style="color:var(--sage);font-weight:600;font-size:0.85rem;">✓ Applied for this session.</div>', unsafe_allow_html=True)
