export interface Collection {
  id: string;
  name: string;
  description?: string;
  document_count: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentChunk {
  id: string;
  chunk_index: number;
  page_number?: number;
  content: string;
  token_count: number;
  metadata?: Record<string, any>;
}

export interface DocumentItem {
  id: string;
  filename: string;
  file_size: number;
  file_type: string;
  file_hash: string;
  page_count: number;
  chunk_count: number;
  status: 'uploading' | 'queued' | 'processing' | 'indexed' | 'failed';
  error_message?: string;
  collection_id?: string;
  created_at: string;
  updated_at: string;
  chunks?: DocumentChunk[];
}

export interface CitationItem {
  citation_id: string;
  document_id: string;
  document_title: string;
  chunk_id: string;
  page_number?: number;
  excerpt: string;
  score: number;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sources: CitationItem[];
  confidence?: 'high' | 'medium' | 'low' | 'insufficient_evidence';
  retrieval_mode?: string;
  latency_ms?: number;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  collection_id?: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  messages?: Message[];
}

export interface EvaluationQuestionResult {
  question_id: string;
  question: string;
  expected_answer: string;
  predicted_answer: string;
  is_answerable: boolean;
  relevant_chunk_ids: string[];
  retrieved_chunk_ids: string[];
  retrieval_hit: boolean;
  reciprocal_rank: number;
  citation_valid: boolean;
  faithfulness_score: number;
  latency_ms: number;
}

export interface EvaluationRun {
  id: string;
  name: string;
  retrieval_mode: string;
  total_questions: number;
  recall_at_k: number;
  mrr: number;
  context_precision: number;
  faithfulness: number;
  citation_support_rate: number;
  avg_latency_ms: number;
  error_rate: number;
  status: string;
  created_at: string;
  results?: EvaluationQuestionResult[];
}

export interface SystemSettings {
  app_name: string;
  app_version: string;
  embedding_model: string;
  chunk_size: number;
  chunk_overlap: number;
  top_k: number;
  candidate_k: number;
  rrf_k: number;
  similarity_threshold: number;
  reranking_enabled: boolean;
  llm_provider: string;
  llm_model: string;
  max_upload_size_mb: number;
  database_type: string;
  vector_store_type: string;
  total_documents: number;
  total_chunks: number;
  total_collections: number;
}

export interface HealthStatus {
  status: string;
  app_name: string;
  version: string;
  database_connected: boolean;
  vector_store_ready: boolean;
  indexed_vector_count: number;
  llm_provider: string;
  embedding_model: string;
}
