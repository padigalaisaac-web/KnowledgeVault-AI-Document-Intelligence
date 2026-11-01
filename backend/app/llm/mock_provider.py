"""Deterministic offline Mock LLM provider for zero-cost testing and offline development."""
import re
from typing import List, Dict, Any, Optional
from app.llm.base import LLMProvider


class MockProvider(LLMProvider):
    """
    Offline deterministic LLM provider that extracts grounded answers from provided context
    and generates citations in the required format: [cite:doc_id:chunk_id].
    """

    def generate(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.1
    ) -> str:
        return self._synthesize_answer(prompt)

    def _synthesize_answer(self, prompt: str) -> str:
        # Extract <context> block safely
        context_str = ""
        if "<context>" in prompt and "</context>" in prompt:
            context_str = prompt.split("<context>")[1].split("</context>")[0].strip()

        # Extract user query
        query = ""
        if "User Question:" in prompt:
            after_q = prompt.split("User Question:")[1]
            if "Answer" in after_q:
                query = after_q.split("Answer")[0].strip()
            else:
                query = after_q.strip()
        query_lower = query.lower()

        if not context_str or "No relevant document passages were found." in context_str:
            return "The uploaded documents do not contain sufficient information to answer this question."

        # Parse context blocks separated by \n---\n
        raw_blocks = context_str.split("\n---\n")
        parsed_chunks = []

        for block in raw_blocks:
            lines = block.strip().split("\n")
            if not lines:
                continue
            header = lines[0]
            content = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

            doc_m = re.search(r"\[DOCUMENT_ID:\s*([^\]]+)\]", header)
            chunk_m = re.search(r"\[CHUNK_ID:\s*([^\]]+)\]", header)
            page_m = re.search(r"\[PAGE:\s*([^\]]+)\]", header)

            doc_id = doc_m.group(1).strip() if doc_m else "doc"
            chunk_id = chunk_m.group(1).strip() if chunk_m else "c0"
            page_num = page_m.group(1).strip() if page_m else "1"

            if content:
                parsed_chunks.append((doc_id, chunk_id, page_num, content))

        if not parsed_chunks:
            return "The uploaded documents do not contain sufficient information to answer this question."

        # Check for unanswerable questions (e.g. absent topics)
        all_content = " ".join([c[3].lower() for c in parsed_chunks])
        stop_words = {"what", "which", "how", "explain", "tell", "show", "describe", "compare", "does", "with", "from", "that", "this", "according", "the", "and", "for", "are"}
        q_keywords = [w for w in re.findall(r"\b[a-zA-Z]{3,}\b", query_lower) if w not in stop_words]

        matches_found = [k for k in q_keywords if k in all_content]
        if q_keywords and len(matches_found) == 0:
            return "The uploaded documents do not contain sufficient information to answer this question."

        # Score parsed chunks
        scored_chunks = []
        for doc_id, chunk_id, page_num, content in parsed_chunks:
            c_lower = content.lower()
            score = sum(1 for k in q_keywords if k in c_lower)
            if score > 0:
                scored_chunks.append((score, doc_id, chunk_id, page_num, content))

        if not scored_chunks:
            return "The uploaded documents do not contain sufficient information to answer this question."

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = scored_chunks[:3]

        # Synthesize evidence-backed response
        paragraphs = []
        cites_used = []

        for _, doc_id, chunk_id, page_num, content in top_chunks[:3]:
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", content) if len(s.strip()) > 15]
            if sentences:
                selected_sentence = sentences[0]
                if len(sentences) > 1 and len(selected_sentence) < 120:
                    selected_sentence += " " + sentences[1]
                paragraphs.append(f"{selected_sentence} [cite:{doc_id}:{chunk_id}]")
                cites_used.append(f"[cite:{doc_id}:{chunk_id}]")

        if not paragraphs:
            return "The uploaded documents do not contain sufficient information to answer this question."

        primary_chunk = top_chunks[0]
        primary_doc_id = primary_chunk[1]
        primary_chunk_id = primary_chunk[2]
        primary_page = primary_chunk[3]

        # Extract 2-3 key terms for the diagram
        diagram_nodes = []
        for i, (_, doc_id, chunk_id, page_num, content) in enumerate(top_chunks[:3]):
            # Get first 3-5 words of the sentence as node label
            first_words = re.findall(r"\b[A-Za-z0-9-]+\b", content)[:4]
            label = " ".join(first_words) if first_words else f"Evidence Item {i+1}"
            safe_label = re.sub(r'["\';:]', '', label)
            diagram_nodes.append((f"Node{i+1}", safe_label, f"Page {page_num}"))

        # Build clean, valid Mermaid diagram
        clean_q = re.sub(r'["\';:]', '', query[:28]).strip() or "Research Query"
        mermaid_lines = [
            "```mermaid",
            "flowchart TD",
            f'    Q["🔍 Query: {clean_q}"] --> C["📚 Retrieved Document Evidence"]',
        ]
        for node_id, label, p_label in diagram_nodes:
            mermaid_lines.append(f'    C --> {node_id}["📄 {label} ({p_label})"]')
            mermaid_lines.append(f'    {node_id} --> S["✨ Grounded Conclusion"]')
        mermaid_lines.append("```")
        diagram_block = "\n".join(mermaid_lines)

        # Assemble deeply explainable, structured response
        response_parts = [
            f"### Executive Summary",
            f"Based on the verified passages in the document repository, here is the evidence regarding **{query}**:\n",
            paragraphs[0],
            f"\n### Analytical Breakdown & Evidence",
        ]

        if len(paragraphs) > 1:
            for p in paragraphs[1:]:
                response_parts.append(f"- {p}")
        else:
            response_parts.append(f"- Verified statement: {paragraphs[0]}")

        response_parts.extend([
            f"\n### Visual Concept Flow",
            f"The following diagram illustrates the relationship between the retrieved source evidence and the synthesized conclusion:\n",
            diagram_block,
            f"\n### Evidence Provenance & Synthesis",
            f"In summary, the retrieved evidence directly confirms these findings from source page {primary_page} [cite:{primary_doc_id}:{primary_chunk_id}]. All assertions are grounded strictly in the uploaded text."
        ])

        return "\n\n".join(response_parts)
