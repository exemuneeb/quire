# 📖 Quire — Grounded answers from your own documents

An end-to-end **Retrieval-Augmented Generation** system built **100% from scratch in native Python** — no LangChain, no LlamaIndex. Connect documents or web pages, ask questions in a clean editorial-style interface, and get answers traced back to a passage — or a clear "I don't know" when the answer isn't there.

![theme](https://img.shields.io/badge/UI-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![chroma](https://img.shields.io/badge/Vector%20DB-ChromaDB-14b8a6?style=for-the-badge)
![groq](https://img.shields.io/badge/LLM-Groq%20API-f59e0b?style=for-the-badge)

---

## Key Features

- **100% native pipeline** — no high-level RAG frameworks; every stage (loading, chunking, embedding, retrieval, generation) is plain Python you can read end-to-end.
- **Multi-format ingestion** — PDF (with OCR fallback for scanned pages), DOCX, TXT, and live web pages.
- **Local dense embeddings** — SentenceTransformer models (`all-MiniLM-L6-v2`, `bge-small-en-v1.5`, `all-mpnet-base-v2`) run locally, no external embedding API.
- **ChromaDB persistent vector store** — cosine similarity + a lightweight MMR-style diversified search, with true delete-on-remove per source.
- **Groq inference** — direct REST calls to Groq's LPU-backed chat completions API (`llama-3.3-70b-versatile` by default).
- **Grounding Confidence Index (GCI)** — a fast, dependency-free heuristic that flags likely hallucinations by measuring lexical overlap between the answer and retrieved context.
- **Insights page** — latency breakdown, GCI trend, source distribution, and system health, all in one dedicated view.

---

## Architecture

```
User ─▶ Quire (Streamlit UI) ─▶ SourceManager (registry + ingestion)
                            │
                            ▼
                    DocumentLoader → TextChunker → LocalEmbedder
                            │
                            ▼
                       ChromaDB (persisted)
                            ▲
                            │
        query ─▶ Retriever ┘  (cosine search / MMR, distance-thresholded)
                            │
                            ▼
                     GroqClient (LLM generation)
                            │
                            ▼
                PerformanceMonitor (GCI + latency telemetry)
```

---

## Repository Structure

```
quire/
├── data/                       # local storage (chroma db, uploads, logs) — gitignored
├── intake/
│   ├── loaders.py              # PDF / DOCX / TXT / URL extractors (+ OCR fallback)
│   ├── chunker.py               # pure-Python recursive text splitter
│   └── source_manager.py        # registry + ingestion coordinator
├── vectorize/
│   └── manager.py                # local SentenceTransformer wrapper
├── store/
│   └── vector_store.py           # ChromaDB persistent-client adapter
├── engine/
│   ├── retriever.py               # similarity/MMR search + distance filtering
│   ├── prompts.py                 # grounding-first system prompts
│   └── llm.py                     # native Groq REST client (sync + streaming)
├── telemetry/
│   └── performance_monitor.py     # GCI scoring + telemetry logging
├── interface/
│   ├── app.py                     # Streamlit 5-page interface (Ask · Library · Connect · Insights · Tuning)
│   └── styles.py                  # warm editorial design system (serif headings, paper theme)
├── tests/                         # pytest suite
├── config.py
├── .env.example
├── requirements.txt
└── README.md
```

---

## Pages

| Nav item | What it does |
|---|---|
| **Ask** | The chat interface — ask questions, get grounded answers with source passages and a grounding score. |
| **Library** | Registry of every indexed source — size, chunk count, and one-click removal. |
| **Connect** | Upload files or index a web page. |
| **Insights** | Latency, grounding trend, source distribution, and system health. |
| **Tuning** | Model, embedding, and retrieval parameters for the current session. |

---

## Quickstart

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure your API key
```bash
cp .env.example .env
# then edit .env and set GROQ_API_KEY (free key: https://console.groq.com/keys)
```

### 3. Run the app
```bash
streamlit run interface/app.py
```
Open `http://localhost:8501`.

---

## Running Tests

```bash
pytest tests/
```

---

## License

MIT.
