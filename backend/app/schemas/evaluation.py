"""Pydantic schemas for RAG evaluation benchmarks."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class EvaluationRunRequest(BaseModel):
    name: Optional[str] = "Benchmark Experiment"
    retrieval_mode: str = Field("hybrid", description="dense, hybrid, or hybrid_rerank")
    top_k: int = Field(5, ge=1, le=20)
    dataset_name: Optional[str] = "benchmark_default"


class EvaluationQuestionResult(BaseModel):
    question_id: str
    question: str
    expected_answer: str
    predicted_answer: str
    is_answerable: bool
    relevant_chunk_ids: List[str]
    retrieved_chunk_ids: List[str]
    retrieval_hit: bool
    reciprocal_rank: float
    citation_valid: bool
    faithfulness_score: float
    latency_ms: float


class EvaluationRunResponse(BaseModel):
    id: str
    name: str
    retrieval_mode: str
    total_questions: int
    recall_at_k: float
    mrr: float
    context_precision: float
    faithfulness: float
    citation_support_rate: float
    avg_latency_ms: float
    error_rate: float
    status: str
    created_at: datetime
    results: List[EvaluationQuestionResult] = []
    model_config = ConfigDict(from_attributes=True)
