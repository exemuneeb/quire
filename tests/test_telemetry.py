import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telemetry.performance_monitor import PerformanceMonitor


def make_monitor():
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    os.remove(tmp.name)
    return PerformanceMonitor(log_file=tmp.name)


def test_gci_grounded_refusal_scores_high():
    monitor = make_monitor()
    result = monitor.compute_gci_metrics(
        "I don't have enough information in the connected knowledge base to answer that.",
        [{"content": "irrelevant context"}],
    )
    assert result["risk_level"] == "GROUNDED_REFUSAL"
    assert result["gci_score"] == 1.0


def test_gci_no_chunks_is_high_risk():
    monitor = make_monitor()
    result = monitor.compute_gci_metrics("Some answer.", [])
    assert result["risk_level"] == "HIGH_RISK"


def test_gci_lexical_overlap_scores_grounded_answer_well():
    monitor = make_monitor()
    chunks = [{"content": "The mitochondria is the powerhouse of the cell."}]
    answer = "The mitochondria is the powerhouse of the cell."
    result = monitor.compute_gci_metrics(answer, chunks)
    assert result["gci_score"] > 0.8


def test_log_query_event_persists_entry():
    monitor = make_monitor()
    entry = monitor.log_query_event(
        query="What is RAG?",
        response="RAG combines retrieval with generation.",
        retrieved_chunks=[{"content": "RAG combines retrieval with generation.", "score": 0.1}],
        retrieval_time_ms=12.0,
        gen_time_ms=340.0,
        embedding_model="all-MiniLM-L6-v2 (384d)",
        llm_model="llama-3.3-70b-versatile",
        active_source_count=1,
    )
    logs = monitor.load_logs()
    assert len(logs) == 1
    assert logs[0]["query_id"] == entry["query_id"]
    assert logs[0]["total_latency_ms"] == 352.0
