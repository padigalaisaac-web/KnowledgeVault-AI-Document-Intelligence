"""Evaluation run database model."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Text, DateTime
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    retrieval_mode = Column(String(50), nullable=False)  # dense, hybrid, hybrid_rerank
    total_questions = Column(Integer, nullable=False, default=0)
    recall_at_k = Column(Float, nullable=False, default=0.0)
    mrr = Column(Float, nullable=False, default=0.0)
    context_precision = Column(Float, nullable=False, default=0.0)
    faithfulness = Column(Float, nullable=False, default=0.0)
    citation_support_rate = Column(Float, nullable=False, default=0.0)
    avg_latency_ms = Column(Float, nullable=False, default=0.0)
    error_rate = Column(Float, nullable=False, default=0.0)
    status = Column(String(50), nullable=False, default="completed")
    results_json = Column(Text, nullable=True)  # Detailed question-level predictions & ground truth
    created_at = Column(DateTime, default=utc_now, nullable=False)
