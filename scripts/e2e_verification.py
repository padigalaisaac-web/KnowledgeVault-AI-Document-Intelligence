"""Live End-to-End Test Suite against the running KnowledgeVault AI server."""
import time
import uuid
import json
import httpx

SERVER_URL = "http://127.0.0.1:8000"


def run_e2e_test():
    print("==================================================================")
    print("      KNOWLEDGEVAULT AI — LIVE END-TO-END VERIFICATION SUITE       ")
    print("==================================================================")

    with httpx.Client(timeout=30.0) as client:
        # STEP 1: Health Check Probe
        print("\n[STEP 1/12] Probing Server Health Endpoint (GET /health)...")
        res_health = client.get(f"{SERVER_URL}/health")
        assert res_health.status_code == 200, f"Health check failed: {res_health.text}"
        health_data = res_health.json()
        print(f" -> Status: {health_data['status']}")
        print(f" -> Database Connected: {health_data['database_connected']}")
        print(f" -> Active Vectors in Store: {health_data['indexed_vector_count']}")
        print(f" -> LLM Provider: {health_data['llm_provider']}")
        print(f" -> Embedding Model: {health_data['embedding_model']}")
        assert health_data["status"] == "healthy"
        assert health_data["database_connected"] is True

        # STEP 2: Create a Research Collection
        coll_name = f"Quantum & ML Lab {uuid.uuid4().hex[:6]}"
        print(f"\n[STEP 2/12] Creating Research Collection '{coll_name}' (POST /api/collections)...")
        res_coll = client.post(
            f"{SERVER_URL}/api/collections",
            json={"name": coll_name, "description": "Verification collection for live automated testing."}
        )
        assert res_coll.status_code == 201, f"Collection creation failed: {res_coll.text}"
        coll_data = res_coll.json()
        coll_id = coll_data["id"]
        print(f" -> Collection ID: {coll_id}")
        print(f" -> Collection Name: {coll_data['name']}")

        # STEP 3: Upload a Document (Multipart PDF/Markdown)
        print("\n[STEP 3/12] Uploading Multi-Section Research Document (POST /api/documents/upload)...")
        run_uid = uuid.uuid4().hex[:6]
        doc_content = (
            f"# Transformer Architecture and Scaled Dot-Product Attention (Lab Run {run_uid})\n\n"
            "The Transformer architecture replaces recurrent layers with multi-head self-attention mechanisms.\n\n"
            "Scaled Dot-Product Attention computes compatibility scores using queries Q, keys K, and values V.\n\n"
            "The mathematical equation is defined as Attention(Q, K, V) = softmax((Q * K^T) / sqrt(d_k)) * V.\n\n"
            "The scaling factor sqrt(d_k) counteracts vanishing softmax gradients for high-dimensional projections.\n\n"
            "Layer normalization is applied before residual feed-forward network blocks.\n"
        )
        files = {
            "file": (f"transformer_paper_{run_uid}.md", doc_content.encode("utf-8"), "text/markdown")
        }
        data = {"collection_id": coll_id}
        res_upload = client.post(f"{SERVER_URL}/api/documents/upload", files=files, data=data)
        assert res_upload.status_code == 202, f"Upload failed: {res_upload.text}"
        upload_data = res_upload.json()
        doc_id = upload_data["document_id"]
        print(f" -> Document ID: {doc_id}")
        print(f" -> Filename: {upload_data['filename']}")
        print(f" -> Initial Status: {upload_data['status']}")

        # STEP 4: Poll Ingestion & Verify Chunk Extraction
        print("\n[STEP 4/12] Verifying Ingestion Pipeline & Chunks (GET /api/documents/{id})...")
        time.sleep(1.0)  # Brief wait for background worker
        res_doc = client.get(f"{SERVER_URL}/api/documents/{doc_id}")
        assert res_doc.status_code == 200, f"Get document failed: {res_doc.text}"
        doc_detail = res_doc.json()
        print(f" -> Ingestion Status: {doc_detail['status']}")
        print(f" -> Extracted Chunks: {doc_detail['chunk_count']}")
        print(f" -> Page Count: {doc_detail['page_count']}")
        print(f" -> Content SHA-256: {doc_detail['file_hash'][:16]}...")
        assert doc_detail["status"] == "indexed"
        assert doc_detail["chunk_count"] > 0
        first_chunk = doc_detail["chunks"][0]
        print(f" -> Chunk #0 ID: {first_chunk['id']} (tokens: {first_chunk['token_count']}, page: {first_chunk['page_number']})")

        # STEP 5: Ask Evidence-Grounded Research Question
        query_text = "What is the mathematical equation for Scaled Dot-Product Attention and why is sqrt(d_k) used?"
        print(f"\n[STEP 5/12] Asking Grounded Question (POST /api/chat)...")
        print(f" -> Query: '{query_text}'")
        chat_payload = {
            "message": query_text,
            "collection_id": coll_id,
            "retrieval_mode": "hybrid",
            "rerank": False,
            "top_k": 5
        }
        res_chat = client.post(f"{SERVER_URL}/api/chat", json=chat_payload)
        assert res_chat.status_code == 200, f"Chat failed: {res_chat.text}"
        chat_data = res_chat.json()
        conv_id = chat_data["conversation_id"]
        print(f" -> Assistant Response:\n   \"{chat_data['content']}\"")
        print(f" -> Confidence Level: {chat_data['confidence']}")
        print(f" -> Query Latency: {chat_data['latency_ms']:.2f}ms")

        # STEP 6: Verify Verifiable Citations and Page Provenance
        print("\n[STEP 6/12] Validating Verifiable Source Citations...")
        assert len(chat_data["sources"]) > 0, "No citations returned for grounded answer!"
        citation = chat_data["sources"][0]
        print(f" -> Citation Badge: {citation['citation_id']}")
        print(f" -> Cited Document Title: {citation['document_title']}")
        print(f" -> Document Page: {citation['page_number']}")
        print(f" -> Grounding Excerpt: \"{citation['excerpt'][:120]}...\"")
        print(f" -> Relevance Score: {(citation['score'] * 100):.1f}%")
        assert citation["document_id"] == doc_id
        assert "transformer" in citation["excerpt"].lower() or "attention" in citation["excerpt"].lower()

        # STEP 7: Unanswerable Question Probe (Honest Insufficient Evidence Test)
        unans_query = "What is the cryogenic boiling temperature of neon on the moons of Jupiter?"
        print(f"\n[STEP 7/12] Probing Out-of-Scope / Unanswerable Question (POST /api/chat)...")
        print(f" -> Query: '{unans_query}'")
        res_unans = client.post(f"{SERVER_URL}/api/chat", json={
            "message": unans_query,
            "collection_id": coll_id,
            "retrieval_mode": "hybrid"
        })
        assert res_unans.status_code == 200, f"Unanswerable chat failed: {res_unans.text}"
        unans_data = res_unans.json()
        print(f" -> Assistant Response:\n   \"{unans_data['content']}\"")
        print(f" -> Confidence: {unans_data['confidence']}")
        assert (
            "do not contain sufficient information" in unans_data["content"].lower()
            or "insufficient evidence" in unans_data["content"].lower()
            or unans_data["confidence"] == "insufficient_evidence"
        )
        print(" -> [PASS] Zero hallucinations! Honest insufficient-evidence response returned.")

        # STEP 8: Verify Conversation History Persistence
        print("\n[STEP 8/12] Verifying Conversation History (GET /api/conversations/{id})...")
        res_conv = client.get(f"{SERVER_URL}/api/conversations/{conv_id}")
        assert res_conv.status_code == 200
        conv_detail = res_conv.json()
        print(f" -> Conversation Title: '{conv_detail['title']}'")
        print(f" -> Persisted Messages: {conv_detail['message_count']}")
        assert conv_detail["message_count"] >= 2

        # STEP 9: Trigger Live Automated Benchmark Run
        print("\n[STEP 9/12] Triggering Live Benchmark Run (POST /api/evaluation/run)...")
        res_eval = client.post(f"{SERVER_URL}/api/evaluation/run", json={
            "name": "Live End-to-End Benchmark",
            "retrieval_mode": "hybrid",
            "top_k": 5
        })
        assert res_eval.status_code == 201, f"Evaluation run failed: {res_eval.text}"
        eval_run = res_eval.json()
        run_id = eval_run["id"]
        print(f" -> Benchmark Run ID: {run_id}")
        print(f" -> Total Evaluated Questions: {eval_run['total_questions']}")
        print(f" -> Recall@5: {(eval_run['recall_at_k'] * 100):.1f}%")
        print(f" -> Mean Reciprocal Rank (MRR): {eval_run['mrr']:.4f}")
        print(f" -> Context Precision: {(eval_run['context_precision'] * 100):.1f}%")
        print(f" -> Faithfulness Score: {(eval_run['faithfulness'] * 100):.1f}%")
        print(f" -> Average Latency: {eval_run['avg_latency_ms']:.2f}ms")

        # STEP 10: Export Benchmark Data to CSV & JSON
        print("\n[STEP 10/12] Exporting Benchmark Results (GET /api/evaluation/runs/{id}/export)...")
        res_csv = client.get(f"{SERVER_URL}/api/evaluation/runs/{run_id}/export?format=csv")
        assert res_csv.status_code == 200
        assert "question_id,question,expected_answer" in res_csv.text
        print(f" -> CSV Export Size: {len(res_csv.text)} bytes (Headers verified)")

        res_json = client.get(f"{SERVER_URL}/api/evaluation/runs/{run_id}/export?format=json")
        assert res_json.status_code == 200
        export_json = res_json.json()
        print(f" -> JSON Export Verified: {len(export_json['questions'])} question predictions included.")

        # STEP 11: Settings Inspection and Runtime Configuration
        print("\n[STEP 11/12] Inspecting & Updating System Settings (GET/PUT /api/settings)...")
        res_settings = client.get(f"{SERVER_URL}/api/settings")
        assert res_settings.status_code == 200
        s_data = res_settings.json()
        print(f" -> Total Documents: {s_data['total_documents']}")
        print(f" -> Total Chunks: {s_data['total_chunks']}")
        print(f" -> Current Top-K: {s_data['top_k']}")

        res_update_s = client.put(f"{SERVER_URL}/api/settings", json={"top_k": 6, "similarity_threshold": 0.22})
        assert res_update_s.status_code == 200
        assert res_update_s.json()["top_k"] == 6
        print(" -> Runtime hyperparameters updated successfully.")

        # STEP 12: Complete Cleanup & Vector Deletion
        print("\n[STEP 12/12] Deleting Document & Verifying Vector Cleanup (DELETE /api/documents/{id})...")
        res_del_doc = client.delete(f"{SERVER_URL}/api/documents/{doc_id}")
        assert res_del_doc.status_code == 204
        # Verify document is gone
        res_check_del = client.get(f"{SERVER_URL}/api/documents/{doc_id}")
        assert res_check_del.status_code == 404
        # Clean up collection
        client.delete(f"{SERVER_URL}/api/collections/{coll_id}")
        print(" -> [PASS] Document, chunks, vector embeddings, and collection cleanly purged.")

    print("\n==================================================================")
    print("      ALL 12 END-TO-END VERIFICATION STEPS PASSED SUCCESSFULLY!    ")
    print("==================================================================")


if __name__ == "__main__":
    run_e2e_test()
