import React from 'react';
import { X, FileText, Bookmark, ExternalLink } from 'lucide-react';
import { CitationItem } from '../types';

interface SourceDrawerProps {
  citation: CitationItem | null;
  onClose: () => void;
}

export const SourceDrawer: React.FC<SourceDrawerProps> = ({ citation, onClose }) => {
  if (!citation) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm transition-opacity">
      <div 
        className="w-full max-w-lg bg-surface-900 border-l border-surface-800 h-full flex flex-col shadow-2xl animate-in slide-in-from-right duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-5 border-b border-surface-800 flex items-center justify-between bg-surface-950/40">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Bookmark className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-mono text-xs font-bold text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                  {citation.citation_id}
                </span>
                <h3 className="text-sm font-semibold text-surface-100">Verified Citation</h3>
              </div>
              <p className="text-[11px] text-surface-400 font-mono mt-0.5">Page-Level Provenance</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-surface-400 hover:text-surface-100 hover:bg-surface-800 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Details */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-xs">
          {/* Metadata Card */}
          <div className="p-4 rounded-xl bg-surface-950/60 border border-surface-800/80 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-surface-500 font-mono uppercase text-[10px]">Document</span>
              <span className="font-medium text-surface-200 truncate max-w-[220px]" title={citation.document_title}>
                {citation.document_title}
              </span>
            </div>
            <div className="flex items-center justify-between border-t border-surface-800/60 pt-2">
              <span className="text-surface-500 font-mono uppercase text-[10px]">Physical Page</span>
              <span className="font-mono text-emerald-400 font-semibold">
                {citation.page_number ? `Page ${citation.page_number}` : 'Full Document'}
              </span>
            </div>
            <div className="flex items-center justify-between border-t border-surface-800/60 pt-2">
              <span className="text-surface-500 font-mono uppercase text-[10px]">Chunk Identifier</span>
              <span className="font-mono text-surface-400 text-[10px] truncate max-w-[180px]">
                {citation.chunk_id}
              </span>
            </div>
            <div className="flex items-center justify-between border-t border-surface-800/60 pt-2">
              <span className="text-surface-500 font-mono uppercase text-[10px]">Fusion Relevance</span>
              <span className="font-mono text-surface-300">
                {(citation.score * 100).toFixed(1)}% match
              </span>
            </div>
          </div>

          {/* Verbatim Excerpt */}
          <div className="space-y-2">
            <label className="text-surface-400 font-semibold tracking-wide uppercase text-[10px] font-mono block">
              Verbatim Retrieved Text Passages
            </label>
            <div className="p-4 rounded-xl bg-surface-950 border border-surface-800 text-surface-300 leading-relaxed font-sans whitespace-pre-wrap select-text">
              {citation.excerpt}
            </div>
            <p className="text-[11px] text-surface-500 italic">
              Extracted directly from source file during ingestion. Verified by CitationValidator.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-surface-800 bg-surface-950/40 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-surface-800 hover:bg-surface-700 text-surface-200 text-xs font-medium transition"
          >
            Close Source
          </button>
        </div>
      </div>
    </div>
  );
};
