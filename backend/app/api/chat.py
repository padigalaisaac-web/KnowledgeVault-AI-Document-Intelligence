"""API endpoints for conversational research chat and message history."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.conversation import Conversation, Message
from app.schemas.chat import (
    ChatRequest,
    MessageResponse,
    ConversationResponse,
    ConversationCreate,
    CitationItem
)
from app.services.rag_service import RAGService
import json

router = APIRouter(prefix="", tags=["Research Chat"])


@router.post("/api/chat", response_model=MessageResponse)
def chat_query(payload: ChatRequest, db: Session = Depends(get_db)):
    """
    Ask a research question.
    Retrieves evidence from user documents, generates evidence-grounded answer,
    verifies source citations, and persists conversation.
    """
    response = RAGService.ask(
        db=db,
        query=payload.message,
        conversation_id=payload.conversation_id,
        collection_id=payload.collection_id,
        retrieval_mode=payload.retrieval_mode,
        rerank=payload.rerank,
        top_k=payload.top_k
    )
    return response


@router.get("/api/conversations", response_model=List[ConversationResponse])
def list_conversations(db: Session = Depends(get_db)):
    """List recent conversation threads."""
    conversations = db.query(Conversation).order_by(Conversation.updated_at.desc()).all()
    results = []
    for c in conversations:
        msg_count = db.query(Message).filter(Message.conversation_id == c.id).count()
        results.append(ConversationResponse(
            id=c.id,
            title=c.title,
            collection_id=c.collection_id,
            created_at=c.created_at,
            updated_at=c.updated_at,
            message_count=msg_count,
            messages=[]
        ))
    return results


@router.post("/api/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(payload: ConversationCreate, db: Session = Depends(get_db)):
    """Create a new research conversation."""
    conv = Conversation(
        title=payload.title or "New Research Chat",
        collection_id=payload.collection_id
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)

    return ConversationResponse(
        id=conv.id,
        title=conv.title,
        collection_id=conv.collection_id,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=0,
        messages=[]
    )


@router.get("/api/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Get conversation details and full message history with citations."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    messages = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at.asc()).all()
    msg_responses = []
    for m in messages:
        sources_list = []
        if m.sources_json:
            try:
                raw_sources = json.loads(m.sources_json)
                sources_list = [CitationItem(**s) for s in raw_sources]
            except Exception:
                sources_list = []

        msg_responses.append(MessageResponse(
            id=m.id,
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            sources=sources_list,
            confidence=m.confidence,
            retrieval_mode=m.retrieval_mode,
            latency_ms=m.latency_ms,
            created_at=m.created_at
        ))

    return ConversationResponse(
        id=conv.id,
        title=conv.title,
        collection_id=conv.collection_id,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=len(msg_responses),
        messages=msg_responses
    )


@router.delete("/api/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Delete a conversation thread and all its messages."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    db.delete(conv)
    db.commit()
    return None
