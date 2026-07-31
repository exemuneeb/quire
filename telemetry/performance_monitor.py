import os
import json
import time
from typing import List, Dict, Any, Optional

from config import PERFORMANCE_LOG_FILE


class PerformanceMonitor:
    """Telemetry logger + Grounding Confidence Index (GCI) evaluator.

    GCI is a lightweight, dependency-free heuristic: lexical overlap between
    the generated answer and the retrieved context, used as a fast proxy for
    "is this answer actually grounded in what we retrieved". It is not a
    substitute for a proper LLM-judged faithfulness eval, but it's free,
    instant, and good enough to flag likely hallucinations in a dashboard.
    """

    def __init__(self, log_file: str = PERFORMANCE_LOG_FILE):
        self.log_file = log_file
        if not os.path.exists(self.log_file):
            self._write([])

    def _write(self, logs: List[Dict[str, Any]]) -> None:
        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)

    def load_logs(self) -> List[Dict[str, Any]]:
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def compute_gci_metrics(self, response: str, retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute Grounding Confidence Index, lexical overlap, citation density, risk level."""
        if not response or not retrieved_chunks:
            return {"gci_score": 0.0, "lexical_overlap": 0.0, "citation_density": 0.0, "risk_level": "HIGH_RISK"}

        lowered = response.lower()
        if "don't have enough information" in lowered or "do not have enough information" in lowered:
            return {"gci_score": 1.0, "lexical_overlap": 1.0, "citation_density": 0.0, "risk_level": "GROUNDED_REFUSAL"}

        context_text = " ".join(c.get("content", "") for c in retrieved_chunks).lower()
        response_words = [w.strip(".,!?\"'()[]") for w in lowered.split() if len(w) > 3]

        if not response_words:
            return {"gci_score": 1.0, "lexical_overlap": 1.0, "citation_density": 0.0, "risk_level": "GROUNDED_REFUSAL"}

        matches = sum(1 for w in response_words if w in context_text)
        lexical_overlap = round(matches / len(response_words), 2)

        citation_markers = response.count(".pdf") + response.count(".docx") + response.count(".txt") + response.count("Source:")
        total_words = max(1, len(response.split()))
        citation_density = round((citation_markers / total_words) * 100, 2)

        gci_score = min(1.0, max(0.0, lexical_overlap * 1.15))
        if gci_score >= 0.70:
            risk_level = "LOW_RISK"
        elif gci_score >= 0.40:
            risk_level = "MODERATE_RISK"
        else:
            risk_level = "HIGH_RISK"

        return {
            "gci_score": round(gci_score, 2),
            "lexical_overlap": lexical_overlap,
            "citation_density": citation_density,
            "risk_level": risk_level,
        }

    def log_query_event(
        self,
        query: str,
        response: str,
        retrieved_chunks: List[Dict[str, Any]],
        retrieval_time_ms: float,
        gen_time_ms: float,
        embedding_model: str,
        llm_model: str,
        active_source_count: int,
        compression_stats: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        total_latency_ms = retrieval_time_ms + gen_time_ms
        scores = [item.get("score", 0.0) for item in retrieved_chunks]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        top_score = scores[0] if scores else 0.0
        compression_stats = compression_stats or {}
        gci = self.compute_gci_metrics(response, retrieved_chunks)

        entry = {
            "query_id": f"q_{int(time.time() * 1000)}",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "query": query,
            "response": response,
            "nodes_retrieved": len(retrieved_chunks),
            "retrieval_latency_ms": round(retrieval_time_ms, 2),
            "generation_latency_ms": round(gen_time_ms, 2),
            "total_latency_ms": round(total_latency_ms, 2),
            "avg_distance_score": round(avg_score, 4),
            "top_distance_score": round(top_score, 4),
            "grounding_confidence_index": gci["gci_score"],
            "lexical_overlap_ratio": gci["lexical_overlap"],
            "citation_density": gci["citation_density"],
            "hallucination_risk": gci["risk_level"],
            "vector_db": "ChromaDB",
            "embedding_model": embedding_model,
            "llm_model": llm_model,
            "active_source_count": active_source_count,
            "payload_chars": compression_stats.get("payload_char_count", 0),
        }

        logs = self.load_logs()
        logs.append(entry)
        self._write(logs)
        return entry

    def clear_logs(self) -> None:
        self._write([])
