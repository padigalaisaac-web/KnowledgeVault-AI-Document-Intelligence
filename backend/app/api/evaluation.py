"""API endpoints for automated RAG evaluation runs and exports."""
import csv
import io
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.evaluation import EvaluationRun
from app.schemas.evaluation import EvaluationRunRequest, EvaluationRunResponse, EvaluationQuestionResult
from app.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/api/evaluation", tags=["Evaluation"])


@router.post("/run", response_model=EvaluationRunResponse, status_code=status.HTTP_201_CREATED)
def trigger_evaluation(payload: EvaluationRunRequest, db: Session = Depends(get_db)):
    """Run an automated evaluation experiment across the benchmark dataset."""
    rerank = (payload.retrieval_mode == "hybrid_rerank")
    run_response = EvaluationService.run_benchmark(
        db=db,
        name=payload.name or "Benchmark Run",
        retrieval_mode=payload.retrieval_mode,
        top_k=payload.top_k,
        rerank=rerank
    )
    return run_response


@router.get("/runs", response_model=List[EvaluationRunResponse])
def list_evaluation_runs(db: Session = Depends(get_db)):
    """List all completed evaluation runs."""
    runs = db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).all()
    results = []
    for r in runs:
        results.append(EvaluationRunResponse(
            id=r.id,
            name=r.name,
            retrieval_mode=r.retrieval_mode,
            total_questions=r.total_questions,
            recall_at_k=r.recall_at_k,
            mrr=r.mrr,
            context_precision=r.context_precision,
            faithfulness=r.faithfulness,
            citation_support_rate=r.citation_support_rate,
            avg_latency_ms=r.avg_latency_ms,
            error_rate=r.error_rate,
            status=r.status,
            created_at=r.created_at,
            results=[]
        ))
    return results


@router.get("/runs/{run_id}", response_model=EvaluationRunResponse)
def get_evaluation_run(run_id: str, db: Session = Depends(get_db)):
    """Get full details of a specific evaluation run including question predictions."""
    r = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation run not found")

    detailed_results = []
    if r.results_json:
        try:
            raw_items = json.loads(r.results_json)
            detailed_results = [EvaluationQuestionResult(**item) for item in raw_items]
        except Exception:
            detailed_results = []

    return EvaluationRunResponse(
        id=r.id,
        name=r.name,
        retrieval_mode=r.retrieval_mode,
        total_questions=r.total_questions,
        recall_at_k=r.recall_at_k,
        mrr=r.mrr,
        context_precision=r.context_precision,
        faithfulness=r.faithfulness,
        citation_support_rate=r.citation_support_rate,
        avg_latency_ms=r.avg_latency_ms,
        error_rate=r.error_rate,
        status=r.status,
        created_at=r.created_at,
        results=detailed_results
    )


@router.get("/runs/{run_id}/export")
def export_evaluation_run(run_id: str, format: str = "json", db: Session = Depends(get_db)):
    """Export benchmark run results in JSON or CSV format."""
    r = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation run not found")

    raw_items = json.loads(r.results_json) if r.results_json else []

    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "question_id", "question", "expected_answer", "predicted_answer",
            "is_answerable", "retrieval_hit", "reciprocal_rank", "citation_valid",
            "faithfulness_score", "latency_ms"
        ])
        for q in raw_items:
            writer.writerow([
                q.get("question_id"),
                q.get("question"),
                q.get("expected_answer"),
                q.get("predicted_answer"),
                q.get("is_answerable"),
                q.get("retrieval_hit"),
                q.get("reciprocal_rank"),
                q.get("citation_valid"),
                q.get("faithfulness_score"),
                q.get("latency_ms")
            ])
        csv_data = output.getvalue()
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=benchmark_run_{run_id}.csv"}
        )

    # JSON export
    export_payload = {
        "id": r.id,
        "name": r.name,
        "retrieval_mode": r.retrieval_mode,
        "total_questions": r.total_questions,
        "recall_at_k": r.recall_at_k,
        "mrr": r.mrr,
        "context_precision": r.context_precision,
        "faithfulness": r.faithfulness,
        "citation_support_rate": r.citation_support_rate,
        "avg_latency_ms": r.avg_latency_ms,
        "error_rate": r.error_rate,
        "created_at": r.created_at.isoformat(),
        "questions": raw_items
    }
    return Response(
        content=json.dumps(export_payload, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=benchmark_run_{run_id}.json"}
    )
