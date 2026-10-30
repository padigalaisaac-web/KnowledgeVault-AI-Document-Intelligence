import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileText,
  Trash2,
  RefreshCw,
  Search,
  Eye,
  CheckCircle2,
  Clock,
  AlertTriangle,
  FolderPlus,
  X,
  FileCheck,
  Layers
} from 'lucide-react';
import { DocumentItem, Collection, DocumentChunk } from '../types';
import { api } from '../services/api';

interface DocumentVaultViewProps {
  documents: DocumentItem[];
  collections: Collection[];
  onRefresh: () => void;
}

export const DocumentVaultView: React.FC<DocumentVaultViewProps> = ({
  documents,
  collections,
  onRefresh,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCollection, setSelectedCollection] = useState<string>('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [selectedDocDetail, setSelectedDocDetail] = useState<DocumentItem | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  
  // New Collection State
  const [isNewCollectionOpen, setIsNewCollectionOpen] = useState(false);
  const [newCollectionName, setNewCollectionName] = useState('');

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];

    const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
    if (!['.pdf', '.txt', '.md', '.markdown'].includes(ext)) {
      setUploadError(`Unsupported format '${ext}'. Supported: .pdf, .txt, .md`);
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      setUploadError('File exceeds 50MB size limit.');
      return;
    }

    setIsUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    try {
      const res = await api.uploadDocument(file, selectedCollection || undefined);
      setUploadSuccess(`Uploaded and indexed '${res.filename}' successfully.`);
      onRefresh();
    } catch (err: any) {
      setUploadError(err.message || 'Upload failed.');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileUpload(e.dataTransfer.files);
  };

  const handleDelete = async (docId: string, filename: string) => {
    if (!confirm(`Delete '${filename}' and remove all associated vector embeddings?`)) return;
    try {
      await api.deleteDocument(docId);
      onRefresh();
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const handleCreateCollection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCollectionName.trim()) return;
    try {
      await api.createCollection(newCollectionName.trim());
      setNewCollectionName('');
      setIsNewCollectionOpen(false);
      onRefresh();
    } catch (err: any) {
      alert(`Create collection error: ${err.message}`);
    }
  };

  const filteredDocs = documents.filter((doc) => {
    const matchesSearch = doc.filename.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCollection = !selectedCollection || doc.collection_id === selectedCollection;
    return matchesSearch && matchesCollection;
  });

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="flex-1 p-4 md:p-6 max-w-6xl mx-auto space-y-6 overflow-y-auto pb-20 md:pb-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-surface-800 pb-5">
        <div>
          <h2 className="text-xl font-bold text-surface-100 tracking-tight">Document Vault</h2>
          <p className="text-xs text-surface-400 mt-1">
            Upload, manage, and inspect indexed research papers and documents.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setIsNewCollectionOpen(true)}
            className="flex items-center space-x-1.5 px-3 py-2 rounded-xl bg-surface-800 hover:bg-surface-700 text-surface-200 text-xs font-medium transition border border-surface-700"
          >
            <FolderPlus className="w-3.5 h-3.5 text-emerald-400" />
            <span>New Collection</span>
          </button>

          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-surface-950 text-xs font-semibold transition shadow-md shadow-emerald-500/10 disabled:opacity-50"
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span>{isUploading ? 'Uploading...' : 'Upload File'}</span>
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt,.md,.markdown"
            onChange={(e) => handleFileUpload(e.target.files)}
            className="hidden"
          />
        </div>
      </div>

      {/* Drag & Drop Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all ${
          isDragging
            ? 'border-emerald-400 bg-emerald-500/5 scale-[0.99]'
            : 'border-surface-800 hover:border-surface-700 bg-surface-900/30'
        }`}
      >
        <div className="flex flex-col items-center space-y-2">
          <div className="w-10 h-10 rounded-xl bg-surface-800 flex items-center justify-center text-surface-300">
            <UploadCloud className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <p className="text-xs font-medium text-surface-200">
              Drop PDF, Markdown, or Text files here, or <span className="text-emerald-400 underline">browse</span>
            </p>
            <p className="text-[11px] text-surface-500 mt-0.5">
              Files are automatically chunked, embedded with 384d MiniLM vectors, and indexed in Qdrant & BM25.
            </p>
          </div>
        </div>
      </div>

      {/* Notifications */}
      {uploadError && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center justify-between">
          <span>{uploadError}</span>
          <button onClick={() => setUploadError(null)}><X className="w-4 h-4" /></button>
        </div>
      )}
      {uploadSuccess && (
        <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center justify-between">
          <span>{uploadSuccess}</span>
          <button onClick={() => setUploadSuccess(null)}><X className="w-4 h-4" /></button>
        </div>
      )}

      {/* Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-72">
          <Search className="w-3.5 h-3.5 absolute left-3 top-3 text-surface-500" />
          <input
            type="text"
            placeholder="Search documents by name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-surface-950 border border-surface-800 rounded-xl pl-9 pr-3 py-2 text-xs text-surface-200 placeholder-surface-500 focus:outline-none focus:border-emerald-500"
          />
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <select
            value={selectedCollection}
            onChange={(e) => setSelectedCollection(e.target.value)}
            className="bg-surface-950 border border-surface-800 rounded-xl px-3 py-2 text-xs text-surface-300 focus:outline-none focus:border-emerald-500"
          >
            <option value="">All Collections ({collections.length})</option>
            {collections.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>

          <button
            onClick={onRefresh}
            className="p-2 rounded-xl bg-surface-900 border border-surface-800 hover:bg-surface-800 text-surface-400 hover:text-surface-200 transition"
            title="Refresh documents"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Documents Table */}
      <div className="bg-surface-900/60 border border-surface-800 rounded-2xl overflow-hidden shadow-xl text-xs">
        <table className="w-full text-left">
          <thead className="bg-surface-950/70 border-b border-surface-800 text-surface-400 font-mono text-[10px] uppercase">
            <tr>
              <th className="p-3.5">Document Name</th>
              <th className="p-3.5">Status</th>
              <th className="p-3.5">Pages</th>
              <th className="p-3.5">Chunks</th>
              <th className="p-3.5">Size</th>
              <th className="p-3.5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-800/60 text-surface-300">
            {filteredDocs.length === 0 ? (
              <tr>
                <td colSpan={6} className="p-8 text-center text-surface-500 italic">
                  No documents found in vault. Upload a PDF or markdown file to start.
                </td>
              </tr>
            ) : (
              filteredDocs.map((doc) => (
                <tr key={doc.id} className="hover:bg-surface-850/40 transition">
                  <td className="p-3.5">
                    <div className="flex items-center space-x-2.5">
                      <FileText className="w-4 h-4 text-emerald-400 shrink-0" />
                      <div>
                        <span className="font-medium text-surface-100">{doc.filename}</span>
                        <div className="text-[10px] font-mono text-surface-500">
                          ID: {doc.id.slice(0, 8)}...
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="p-3.5">
                    <span className="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      <span className="capitalize">{doc.status}</span>
                    </span>
                  </td>
                  <td className="p-3.5 font-mono text-surface-400">{doc.page_count || 1}</td>
                  <td className="p-3.5 font-mono text-emerald-400 font-medium">{doc.chunk_count}</td>
                  <td className="p-3.5 font-mono text-surface-500">{formatFileSize(doc.file_size)}</td>
                  <td className="p-3.5 text-right space-x-1">
                    <button
                      onClick={async () => {
                        const fullDoc = await api.getDocumentDetail(doc.id);
                        setSelectedDocDetail(fullDoc);
                      }}
                      className="p-1.5 rounded-lg text-surface-400 hover:text-surface-100 hover:bg-surface-800 transition"
                      title="Inspect Chunks"
                    >
                      <Eye className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleDelete(doc.id, doc.filename)}
                      className="p-1.5 rounded-lg text-surface-400 hover:text-rose-400 hover:bg-surface-800 transition"
                      title="Delete Document"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Chunk Inspector Modal */}
      {selectedDocDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-2xl bg-surface-900 border border-surface-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[80vh]">
            <div className="p-4 border-b border-surface-800 flex items-center justify-between bg-surface-950/40">
              <div>
                <h3 className="text-sm font-semibold text-surface-100">
                  {selectedDocDetail.filename}
                </h3>
                <p className="text-[11px] text-surface-400 font-mono">
                  {selectedDocDetail.chunk_count} indexed chunks • {selectedDocDetail.page_count} pages
                </p>
              </div>
              <button
                onClick={() => setSelectedDocDetail(null)}
                className="p-1.5 rounded-lg text-surface-400 hover:text-surface-100 hover:bg-surface-800"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 overflow-y-auto space-y-3 flex-1 text-xs">
              {(!selectedDocDetail.chunks || selectedDocDetail.chunks.length === 0) ? (
                <p className="text-surface-500 italic text-center py-6">No chunks found.</p>
              ) : (
                selectedDocDetail.chunks.map((chunk) => (
                  <div key={chunk.id} className="p-3.5 rounded-xl bg-surface-950 border border-surface-800 space-y-2">
                    <div className="flex items-center justify-between text-[10px] font-mono text-surface-500">
                      <span className="text-emerald-400 font-bold">Chunk #{chunk.chunk_index}</span>
                      <span>Page {chunk.page_number || 1} • {chunk.token_count} tokens</span>
                    </div>
                    <p className="text-surface-300 font-sans leading-relaxed whitespace-pre-wrap">
                      {chunk.content}
                    </p>
                  </div>
                ))
              )}
            </div>

            <div className="p-3 border-t border-surface-800 bg-surface-950/40 flex justify-end">
              <button
                onClick={() => setSelectedDocDetail(null)}
                className="px-4 py-1.5 rounded-lg bg-surface-800 text-surface-200 text-xs font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* New Collection Dialog */}
      {isNewCollectionOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-sm bg-surface-900 border border-surface-800 rounded-2xl p-5 space-y-4 shadow-2xl">
            <h3 className="text-sm font-semibold text-surface-100">Create Knowledge Collection</h3>
            <form onSubmit={handleCreateCollection} className="space-y-3 text-xs">
              <div>
                <label className="text-surface-400 block mb-1">Collection Name</label>
                <input
                  type="text"
                  placeholder="e.g. Machine Learning Papers"
                  value={newCollectionName}
                  onChange={(e) => setNewCollectionName(e.target.value)}
                  className="w-full bg-surface-950 border border-surface-800 rounded-xl px-3 py-2 text-surface-100 focus:outline-none focus:border-emerald-500"
                  autoFocus
                />
              </div>
              <div className="flex items-center justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsNewCollectionOpen(false)}
                  className="px-3 py-1.5 rounded-lg bg-surface-800 text-surface-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-emerald-500 text-surface-950 font-semibold"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
