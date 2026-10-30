"""API endpoints for collection management."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.collection import Collection
from app.models.document import Document
from app.schemas.collection import CollectionCreate, CollectionUpdate, CollectionResponse

router = APIRouter(prefix="/api/collections", tags=["Collections"])


@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
def create_collection(payload: CollectionCreate, db: Session = Depends(get_db)):
    """Create a new document collection."""
    existing = db.query(Collection).filter(Collection.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Collection '{payload.name}' already exists."
        )

    coll = Collection(name=payload.name, description=payload.description)
    db.add(coll)
    db.commit()
    db.refresh(coll)

    return CollectionResponse(
        id=coll.id,
        name=coll.name,
        description=coll.description,
        document_count=0,
        created_at=coll.created_at,
        updated_at=coll.updated_at
    )


@router.get("", response_model=List[CollectionResponse])
def list_collections(db: Session = Depends(get_db)):
    """List all document collections with document counts."""
    collections = db.query(Collection).order_by(Collection.created_at.desc()).all()
    results = []
    for c in collections:
        doc_count = db.query(Document).filter(Document.collection_id == c.id).count()
        results.append(CollectionResponse(
            id=c.id,
            name=c.name,
            description=c.description,
            document_count=doc_count,
            created_at=c.created_at,
            updated_at=c.updated_at
        ))
    return results


@router.get("/{collection_id}", response_model=CollectionResponse)
def get_collection(collection_id: str, db: Session = Depends(get_db)):
    """Get single collection details."""
    c = db.query(Collection).filter(Collection.id == collection_id).first()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

    doc_count = db.query(Document).filter(Document.collection_id == c.id).count()
    return CollectionResponse(
        id=c.id,
        name=c.name,
        description=c.description,
        document_count=doc_count,
        created_at=c.created_at,
        updated_at=c.updated_at
    )


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(collection_id: str, db: Session = Depends(get_db)):
    """Delete a collection and its associated documents."""
    c = db.query(Collection).filter(Collection.id == collection_id).first()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

    db.delete(c)
    db.commit()
    return None
