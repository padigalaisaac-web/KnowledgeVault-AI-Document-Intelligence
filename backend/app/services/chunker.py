"""Document chunker preserving document_id, chunk_index, page_number, and content hash."""
import hashlib
import re
from typing import List, Dict, Any, Optional
from app.services.text_extractor import ExtractedPage


class ChunkItem:
    def __init__(
        self,
        chunk_id: str,
        document_id: str,
        chunk_index: int,
        page_number: Optional[int],
        content: str,
        content_hash: str,
        token_count: int,
        metadata: Dict[str, Any],
    ):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.chunk_index = chunk_index
        self.page_number = page_number
        self.content = content
        self.content_hash = content_hash
        self.token_count = token_count
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "page_number": self.page_number,
            "content": self.content,
            "content_hash": self.content_hash,
            "token_count": self.token_count,
            "metadata": self.metadata,
        }


def estimate_tokens(text: str) -> int:
    """Fast token count estimation (~4 characters per token)."""
    if not text:
        return 0
    # Approximate based on words and whitespace
    words = len(text.split())
    chars = len(text)
    return max(1, int((words * 1.3 + chars / 4) / 2))


class DocumentChunker:
    """Sliding-window text chunker respecting paragraph and sentence boundaries."""

    def __init__(self, target_chunk_tokens: int = 700, overlap_tokens: int = 100):
        self.target_chunk_tokens = target_chunk_tokens
        self.overlap_tokens = min(overlap_tokens, target_chunk_tokens // 2)
        # Approximate characters per token = 4
        self.target_chars = target_chunk_tokens * 4
        self.overlap_chars = self.overlap_tokens * 4

    def chunk_pages(
        self,
        document_id: str,
        document_title: str,
        pages: List[ExtractedPage],
        collection_id: Optional[str] = None
    ) -> List[ChunkItem]:
        """Split a list of extracted pages into indexed chunks."""
        chunks: List[ChunkItem] = []
        global_chunk_idx = 0

        for page in pages:
            if page.is_empty or not page.text.strip():
                continue

            # Split page text into natural paragraphs
            paragraphs = [p.strip() for p in page.text.split("\n\n") if p.strip()]
            if not paragraphs:
                paragraphs = [page.text.strip()]

            current_chunk_paras: List[str] = []
            current_length = 0

            for para in paragraphs:
                para_len = len(para)

                # If single paragraph exceeds target characters, split by sentences
                if para_len > self.target_chars:
                    # Flush accumulated paragraphs first
                    if current_chunk_paras:
                        chunk_text = "\n\n".join(current_chunk_paras)
                        chunks.append(self._create_chunk_item(
                            document_id=document_id,
                            document_title=document_title,
                            chunk_index=global_chunk_idx,
                            page_number=page.page_number,
                            content=chunk_text,
                            collection_id=collection_id
                        ))
                        global_chunk_idx += 1
                        current_chunk_paras = []
                        current_length = 0

                    # Split large paragraph by sentences
                    sentences = re.split(r'(?<=[.!?])\s+', para)
                    sub_paras: List[str] = []
                    sub_len = 0
                    for sent in sentences:
                        if sub_len + len(sent) > self.target_chars and sub_paras:
                            chunk_text = " ".join(sub_paras)
                            chunks.append(self._create_chunk_item(
                                document_id=document_id,
                                document_title=document_title,
                                chunk_index=global_chunk_idx,
                                page_number=page.page_number,
                                content=chunk_text,
                                collection_id=collection_id
                            ))
                            global_chunk_idx += 1
                            # Retain overlap sentences if possible
                            overlap_buf: List[str] = []
                            overlap_sz = 0
                            for s in reversed(sub_paras):
                                if overlap_sz + len(s) <= self.overlap_chars:
                                    overlap_buf.insert(0, s)
                                    overlap_sz += len(s)
                                else:
                                    break
                            sub_paras = overlap_buf
                            sub_len = overlap_sz

                        sub_paras.append(sent)
                        sub_len += len(sent)

                    if sub_paras:
                        current_chunk_paras = sub_paras
                        current_length = sub_len
                    continue

                if current_length + para_len > self.target_chars and current_chunk_paras:
                    # Yield chunk
                    chunk_text = "\n\n".join(current_chunk_paras)
                    chunks.append(self._create_chunk_item(
                        document_id=document_id,
                        document_title=document_title,
                        chunk_index=global_chunk_idx,
                        page_number=page.page_number,
                        content=chunk_text,
                        collection_id=collection_id
                    ))
                    global_chunk_idx += 1

                    # Keep last paragraph for overlap if within overlap budget
                    if len(current_chunk_paras[-1]) <= self.overlap_chars:
                        current_chunk_paras = [current_chunk_paras[-1]]
                        current_length = len(current_chunk_paras[0])
                    else:
                        current_chunk_paras = []
                        current_length = 0

                current_chunk_paras.append(para)
                current_length += para_len

            # Flush remaining paragraphs for the page
            if current_chunk_paras:
                chunk_text = "\n\n".join(current_chunk_paras)
                chunks.append(self._create_chunk_item(
                    document_id=document_id,
                    document_title=document_title,
                    chunk_index=global_chunk_idx,
                    page_number=page.page_number,
                    content=chunk_text,
                    collection_id=collection_id
                ))
                global_chunk_idx += 1

        return chunks

    def _create_chunk_item(
        self,
        document_id: str,
        document_title: str,
        chunk_index: int,
        page_number: Optional[int],
        content: str,
        collection_id: Optional[str]
    ) -> ChunkItem:
        chunk_id = f"{document_id}_c{chunk_index}"
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        token_count = estimate_tokens(content)

        metadata = {
            "document_id": document_id,
            "document_title": document_title,
            "page_number": page_number,
            "chunk_index": chunk_index,
            "collection_id": collection_id,
            "token_count": token_count,
        }

        return ChunkItem(
            chunk_id=chunk_id,
            document_id=document_id,
            chunk_index=chunk_index,
            page_number=page_number,
            content=content,
            content_hash=content_hash,
            token_count=token_count,
            metadata=metadata
        )
