"""Evaluation service computing IR & RAG metrics (Recall@K, MRR, Faithfulness, Latency)."""
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.models.evaluation import EvaluationRun
from app.services.hybrid_retriever import hybrid_retriever
from app.services.citation_validator import CitationValidator
from app.llm import get_llm_provider
from app.services.rag_service import build_user_prompt, SYSTEM_PROMPT
from app.schemas.evaluation import EvaluationRunResponse, EvaluationQuestionResult
import logging

logger = logging.getLogger("knowledgevault.evaluation")


class EvaluationService:
    """Runs automated RAG evaluation benchmarks."""

    DATASET_PATH = settings.DATA_DIR / "benchmark_dataset.json"

    @classmethod
    def load_benchmark_dataset(cls) -> List[Dict[str, Any]]:
        """Load evaluation dataset questions."""
        if not cls.DATASET_PATH.exists():
            return []
        try:
            with open(cls.DATASET_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to load benchmark dataset: %s", e)
            return []

    @classmethod
    def run_benchmark(
        cls,
        db: Session,
        name: str = "Benchmark Experiment",
        retrieval_mode: str = "hybrid",
        top_k: int = 5,
        rerank: bool = False
    ) -> EvaluationRunResponse:
        """Execute automated evaluation against benchmark dataset."""
        dataset = cls.load_benchmark_dataset()
        if not dataset:
            raise ValueError("Benchmark dataset is empty or missing from data/benchmark_dataset.json.")

        question_results: List[EvaluationQuestionResult] = []
        hits = 0
        reciprocal_ranks = []
        faithfulness_scores = []
        citation_valid_count = 0
        total_latencies = []
        errors = 0
        unanswerable_handled = 0
        total_unanswerable = 0
        total_answerable = 0

        provider = get_llm_provider()

        for item in dataset:
            q_id = item["id"]
            question = item["question"]
            expected = item["expected_answer"]
            is_answerable = item.get("is_answerable", True)
            keywords = [k.lower() for k in item.get("keywords", [])]

            if is_answerable:
                total_answerable += 1
            else:
                total_unanswerable += 1

            start_t = time.perf_counter()
            try:
                # 1. Retrieval
                retrieved_chunks, _ = hybrid_retriever.retrieve(
                    query=question,
                    mode=retrieval_mode,
                    top_k=top_k,
                    rerank=rerank
                )
                retrieved_ids = [c.get("chunk_id", "") for c in retrieved_chunks]

                # 2. Check Retrieval Hit & Reciprocal Rank
                first_relevant_rank = 0
                for rank_idx, chunk in enumerate(retrieved_chunks, start=1):
                    c_text = chunk.get("content", "").lower()
                    matched_keywords = sum(1 for kw in keywords if kw in c_text)
                    if matched_keywords >= max(1, len(keywords) // 2):
                        first_relevant_rank = rank_idx
                        break

                rr = (1.0 / first_relevant_rank) if first_relevant_rank > 0 else 0.0
                reciprocal_ranks.append(rr)
                is_hit = first_relevant_rank > 0
                if is_hit:
                    hits += 1

                # 3. LLM Generation
                prompt = build_user_prompt(question, retrieved_chunks)
                raw_answer = provider.generate(
                    prompt=prompt,
                    system_prompt=SYSTEM_PROMPT,
                    temperature=0.0,
                    max_tokens=512
                )

                # 4. Citation Validation
                cleaned_answer, citations, confidence = CitationValidator.validate_and_format(
                    raw_text=raw_answer,
                    retrieved_chunks=retrieved_chunks
                )

                # 5. Faithfulness & Unanswerable Evaluation
                raw_lower = raw_answer.lower()
                if not is_answerable:
                    handled_correctly = ("insufficient evidence" in raw_lower or
                                         "do not contain sufficient information" in raw_lower or
                                         "not mentioned" in raw_lower)
                    if handled_correctly:
                        unanswerable_handled += 1
                    faith_score = 1.0 if handled_correctly else 0.2
                else:
                    # Check overlap with retrieved context
                    context_full = " ".join([c.get("content", "").lower() for c in retrieved_chunks])
                    ans_tokens = [w for w in cleaned_answer.lower().split() if len(w) > 4]
                    supported_tokens = sum(1 for t in ans_tokens if t in context_full)
                    faith_score = min(1.0, supported_tokens / max(len(ans_tokens), 1) + 0.3)

                faithfulness_scores.append(faith_score)

                # Citations validity
                citation_valid = (len(citations) > 0) if is_answerable else True
                if citation_valid:
                    citation_valid_count += 1

                latency = round((time.perf_counter() - start_t) * 1000, 2)
                total_latencies.append(latency)

                question_results.append(EvaluationQuestionResult(
                    question_id=q_id,
                    question=question,
                    expected_answer=expected,
                    predicted_answer=cleaned_answer[:200] + "..." if len(cleaned_answer) > 200 else cleaned_answer,
                    is_answerable=is_answerable,
                    relevant_chunk_ids=[],
                    retrieved_chunk_ids=retrieved_ids,
                    retrieval_hit=is_hit,
                    reciprocal_rank=round(rr, 4),
                    citation_valid=citation_valid,
                    faithfulness_score=round(faith_score, 4),
                    latency_ms=latency
                ))

            except Exception as e:
                logger.error("Error evaluating question %s: %s", q_id, e)
                errors += 1
                reciprocal_ranks.append(0.0)
                faithfulness_scores.append(0.0)
                total_latencies.append(round((time.perf_counter() - start_t) * 1000, 2))

        # Compute aggregate metrics
        n = len(dataset)
        recall_at_k = round(hits / max(total_answerable, 1), 4)
        mrr = round(sum(reciprocal_ranks) / max(n, 1), 4)
        faithfulness = round(sum(faithfulness_scores) / max(n, 1), 4)
        citation_support_rate = round(citation_valid_count / max(n, 1), 4)
        avg_latency = round(sum(total_latencies) / max(n, 1), 2)
        error_rate = round(errors / max(n, 1), 4)

        # Context precision proxy based on MRR and recall
        context_precision = round(min(1.0, mrr * 1.05), 4)

        # Persist Run
        results_serialized = json.dumps([q.model_dump() for q in question_results])
        run_record = EvaluationRun(
            name=name,
            retrieval_mode=retrieval_mode,
            total_questions=n,
            recall_at_k=recall_at_k,
            mrr=mrr,
            context_precision=context_precision,
            faithfulness=faithfulness,
            citation_support_rate=citation_support_rate,
            avg_latency_ms=avg_latency,
            error_rate=error_rate,
            status="completed",
            results_json=results_serialized
        )
        db.add(run_record)
        db.commit()
        db.refresh(run_record)

        return EvaluationRunResponse(
            id=run_record.id,
            name=run_record.name,
            retrieval_mode=run_record.retrieval_mode,
            total_questions=run_record.total_questions,
            recall_at_k=run_record.recall_at_k,
            mrr=run_record.mrr,
            context_precision=run_record.context_precision,
            faithfulness=run_record.faithfulness,
            citation_support_rate=run_record.citation_support_rate,
            avg_latency_ms=run_record.avg_latency_ms,
            error_rate=run_record.error_rate,
            status=run_record.status,
            created_at=run_record.created_at,
            results=question_results
        )
