import {
  Collection,
  DocumentItem,
  Conversation,
  Message,
  EvaluationRun,
  SystemSettings,
  HealthStatus
} from '../types';

const API_BASE = '';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorMsg = `HTTP Error ${res.status}: ${res.statusText}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) {
        errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch (_) {
      // ignore
    }
    throw new Error(errorMsg);
  }
  if (res.status === 204) {
    return {} as T;
  }
  return res.json();
}

export const api = {
  // Health
  async getHealth(): Promise<HealthStatus> {
    const res = await fetch(`${API_BASE}/health`);
    return handleResponse<HealthStatus>(res);
  },

  // Collections
  async getCollections(): Promise<Collection[]> {
    const res = await fetch(`${API_BASE}/api/collections`);
    return handleResponse<Collection[]>(res);
  },

  async createCollection(name: string, description?: string): Promise<Collection> {
    const res = await fetch(`${API_BASE}/api/collections`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description }),
    });
    return handleResponse<Collection>(res);
  },

  async deleteCollection(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/collections/${id}`, { method: 'DELETE' });
    return handleResponse<void>(res);
  },

  // Documents
  async getDocuments(collectionId?: string): Promise<DocumentItem[]> {
    const url = collectionId
      ? `${API_BASE}/api/documents?collection_id=${encodeURIComponent(collectionId)}`
      : `${API_BASE}/api/documents`;
    const res = await fetch(url);
    return handleResponse<DocumentItem[]>(res);
  },

  async getDocumentDetail(id: string): Promise<DocumentItem> {
    const res = await fetch(`${API_BASE}/api/documents/${id}`);
    return handleResponse<DocumentItem>(res);
  },

  async uploadDocument(file: File, collectionId?: string): Promise<{ document_id: string; message: string; filename: string }> {
    const formData = new FormData();
    formData.append('file', file);
    if (collectionId) {
      formData.append('collection_id', collectionId);
    }
    const res = await fetch(`${API_BASE}/api/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse(res);
  },

  async deleteDocument(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/documents/${id}`, { method: 'DELETE' });
    return handleResponse<void>(res);
  },

  async reprocessDocument(id: string): Promise<DocumentItem> {
    const res = await fetch(`${API_BASE}/api/documents/${id}/reprocess`, { method: 'POST' });
    return handleResponse<DocumentItem>(res);
  },

  // Research Chat
  async sendChat(
    message: string,
    conversationId?: string,
    collectionId?: string,
    retrievalMode: string = 'hybrid',
    rerank: boolean = false,
    topK: number = 5
  ): Promise<Message> {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
        collection_id: collectionId,
        retrieval_mode: retrievalMode,
        rerank,
        top_k: topK,
      }),
    });
    return handleResponse<Message>(res);
  },

  async getConversations(): Promise<Conversation[]> {
    const res = await fetch(`${API_BASE}/api/conversations`);
    return handleResponse<Conversation[]>(res);
  },

  async getConversation(id: string): Promise<Conversation> {
    const res = await fetch(`${API_BASE}/api/conversations/${id}`);
    return handleResponse<Conversation>(res);
  },

  async createConversation(title?: string, collectionId?: string): Promise<Conversation> {
    const res = await fetch(`${API_BASE}/api/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, collection_id: collectionId }),
    });
    return handleResponse<Conversation>(res);
  },

  async deleteConversation(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/conversations/${id}`, { method: 'DELETE' });
    return handleResponse<void>(res);
  },

  // Evaluation
  async getEvaluationRuns(): Promise<EvaluationRun[]> {
    const res = await fetch(`${API_BASE}/api/evaluation/runs`);
    return handleResponse<EvaluationRun[]>(res);
  },

  async getEvaluationRun(id: string): Promise<EvaluationRun> {
    const res = await fetch(`${API_BASE}/api/evaluation/runs/${id}`);
    return handleResponse<EvaluationRun>(res);
  },

  async triggerEvaluation(name: string, retrievalMode: string = 'hybrid', topK: number = 5): Promise<EvaluationRun> {
    const res = await fetch(`${API_BASE}/api/evaluation/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, retrieval_mode: retrievalMode, top_k: topK }),
    });
    return handleResponse<EvaluationRun>(res);
  },

  getExportUrl(runId: string, format: 'json' | 'csv'): string {
    return `${API_BASE}/api/evaluation/runs/${runId}/export?format=${format}`;
  },

  // Settings
  async getSettings(): Promise<SystemSettings> {
    const res = await fetch(`${API_BASE}/api/settings`);
    return handleResponse<SystemSettings>(res);
  },

  async updateSettings(updates: Partial<SystemSettings>): Promise<SystemSettings> {
    const res = await fetch(`${API_BASE}/api/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
    return handleResponse<SystemSettings>(res);
  },
};
