import {
  Collection,
  DocumentItem,
  Conversation,
  Message,
  EvaluationRun,
  SystemSettings,
  HealthStatus
} from '../types';

export function getApiBase(): string {
  if (typeof window !== 'undefined') {
    const custom = localStorage.getItem('kv_api_url');
    if (custom) return custom.replace(/\/+$/, '');
  }
  const envUrl = (import.meta as any).env?.VITE_API_URL;
  if (envUrl) return envUrl.replace(/\/+$/, '');

  const isNativeMobile = typeof window !== 'undefined' && (
    window.location.protocol === 'capacitor:' || 
    window.location.origin === 'https://localhost' ||
    (window.location.hostname === 'localhost' && window.location.port === '')
  );

  return isNativeMobile ? 'https://knowledgevault-ai.onrender.com' : '';
}

export const API_BASE = getApiBase();

async function fetchWithRetry(path: string, options?: RequestInit, retries = 2, delayMs = 1500): Promise<Response> {
  const base = getApiBase();
  const url = path.startsWith('http') ? path : `${base}${path.startsWith('/') ? '' : '/'}${path}`;
  try {
    const res = await fetch(url, options);
    // Render Free Tier services return 502/503 during cold-boot wake up
    if ((res.status === 502 || res.status === 503 || res.status === 504) && retries > 0) {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
      return fetchWithRetry(path, options, retries - 1, delayMs * 1.5);
    }
    return res;
  } catch (err) {
    if (retries > 0) {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
      return fetchWithRetry(path, options, retries - 1, delayMs * 1.5);
    }
    throw err;
  }
}

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
    const res = await fetchWithRetry('/health');
    return handleResponse<HealthStatus>(res);
  },

  // Collections
  async getCollections(): Promise<Collection[]> {
    const res = await fetchWithRetry('/api/collections');
    return handleResponse<Collection[]>(res);
  },

  async createCollection(name: string, description?: string): Promise<Collection> {
    const res = await fetchWithRetry('/api/collections', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description }),
    });
    return handleResponse<Collection>(res);
  },

  async deleteCollection(id: string): Promise<void> {
    const res = await fetchWithRetry(`/api/collections/${id}`, { method: 'DELETE' });
    return handleResponse<void>(res);
  },

  // Documents
  async getDocuments(collectionId?: string): Promise<DocumentItem[]> {
    const path = collectionId
      ? `/api/documents?collection_id=${encodeURIComponent(collectionId)}`
      : '/api/documents';
    const res = await fetchWithRetry(path);
    return handleResponse<DocumentItem[]>(res);
  },

  async getDocumentDetail(id: string): Promise<DocumentItem> {
    const res = await fetchWithRetry(`/api/documents/${id}`);
    return handleResponse<DocumentItem>(res);
  },

  async uploadDocument(file: File, collectionId?: string): Promise<{ document_id: string; message: string; filename: string }> {
    const formData = new FormData();
    formData.append('file', file);
    if (collectionId) {
      formData.append('collection_id', collectionId);
    }
    const res = await fetchWithRetry('/api/documents/upload', {
      method: 'POST',
      body: formData,
    });
    return handleResponse(res);
  },

  async deleteDocument(id: string): Promise<void> {
    const res = await fetchWithRetry(`/api/documents/${id}`, { method: 'DELETE' });
    return handleResponse<void>(res);
  },

  async reprocessDocument(id: string): Promise<DocumentItem> {
    const res = await fetchWithRetry(`/api/documents/${id}/reprocess`, { method: 'POST' });
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
    const res = await fetchWithRetry('/api/chat', {
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
    const res = await fetchWithRetry('/api/conversations');
    return handleResponse<Conversation[]>(res);
  },

  async getConversation(id: string): Promise<Conversation> {
    const res = await fetchWithRetry(`/api/conversations/${id}`);
    return handleResponse<Conversation>(res);
  },

  async createConversation(title?: string, collectionId?: string): Promise<Conversation> {
    const res = await fetchWithRetry('/api/conversations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, collection_id: collectionId }),
    });
    return handleResponse<Conversation>(res);
  },

  async deleteConversation(id: string): Promise<void> {
    const res = await fetchWithRetry(`/api/conversations/${id}`, { method: 'DELETE' });
    return handleResponse<void>(res);
  },

  // Evaluation
  async getEvaluationRuns(): Promise<EvaluationRun[]> {
    const res = await fetchWithRetry('/api/evaluation/runs');
    return handleResponse<EvaluationRun[]>(res);
  },

  async getEvaluationRun(id: string): Promise<EvaluationRun> {
    const res = await fetchWithRetry(`/api/evaluation/runs/${id}`);
    return handleResponse<EvaluationRun>(res);
  },

  async triggerEvaluation(name: string, retrievalMode: string = 'hybrid', topK: number = 5): Promise<EvaluationRun> {
    const res = await fetchWithRetry('/api/evaluation/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, retrieval_mode: retrievalMode, top_k: topK }),
    });
    return handleResponse<EvaluationRun>(res);
  },

  getExportUrl(runId: string, format: 'json' | 'csv'): string {
    return `${getApiBase()}/api/evaluation/runs/${runId}/export?format=${format}`;
  },

  // Settings
  async getSettings(): Promise<SystemSettings> {
    const res = await fetchWithRetry('/api/settings');
    return handleResponse<SystemSettings>(res);
  },

  async updateSettings(updates: Partial<SystemSettings>): Promise<SystemSettings> {
    const res = await fetchWithRetry('/api/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
    return handleResponse<SystemSettings>(res);
  },
};
