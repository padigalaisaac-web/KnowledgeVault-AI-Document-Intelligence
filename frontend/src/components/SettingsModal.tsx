import React, { useState, useEffect } from 'react';
import { X, Sliders, Cpu, Database, Lock, Check } from 'lucide-react';
import { SystemSettings, HealthStatus } from '../types';
import { api } from '../services/api';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  settings: SystemSettings | null;
  health: HealthStatus | null;
  onRefresh: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  settings,
  health,
  onRefresh,
}) => {
  const [formData, setFormData] = useState<Partial<SystemSettings>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    if (settings) {
      setFormData({
        llm_provider: settings.llm_provider,
        llm_model: settings.llm_model,
        chunk_size: settings.chunk_size,
        top_k: settings.top_k,
      });
    }
  }, [settings]);

  if (!isOpen) return null;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSavedSuccess(false);
    try {
      await api.updateSettings(formData);
      onRefresh();
      setSavedSuccess(true);
      setTimeout(() => {
        setSavedSuccess(false);
        onClose();
      }, 1000);
    } catch (err: any) {
      alert(`Save failed: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div 
        className="w-full max-w-lg bg-surface-900 border border-surface-800 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-5 border-b border-surface-800 flex items-center justify-between bg-surface-950/40">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-surface-800 flex items-center justify-center text-surface-200">
              <Sliders className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-surface-100">System Preferences</h3>
              <p className="text-[11px] text-surface-400">Model adapters & retrieval settings</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-surface-400 hover:text-surface-100 hover:bg-surface-800 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSave} className="p-6 space-y-5 text-xs">
          {/* LLM Provider */}
          <div className="space-y-1.5">
            <label className="text-surface-300 font-medium block">Language Model Provider</label>
            <select
              value={formData.llm_provider || 'mock'}
              onChange={(e) => setFormData({ ...formData, llm_provider: e.target.value })}
              className="w-full bg-surface-950 border border-surface-800 rounded-xl px-3 py-2 text-surface-200 focus:outline-none focus:border-brand-500"
            >
              <option value="mock">Local Offline Adapter (Zero API Cost, Fast)</option>
              <option value="openai">OpenAI (GPT-4o, GPT-4o-mini)</option>
              <option value="anthropic">Anthropic (Claude 3.5 Sonnet)</option>
              <option value="gemini">Google Gemini (Gemini 1.5 Flash)</option>
              <option value="ollama">Ollama (Local Open-Weights Models)</option>
            </select>
            <p className="text-[11px] text-surface-500">
              API credentials are read server-side from your local <code>.env</code> file.
            </p>
          </div>

          {/* Model Identifier */}
          <div className="space-y-1.5">
            <label className="text-surface-300 font-medium block">Model Identifier</label>
            <input
              type="text"
              value={formData.llm_model || ''}
              onChange={(e) => setFormData({ ...formData, llm_model: e.target.value })}
              placeholder="e.g. gpt-4o-mini, claude-3-5-sonnet, llama3.2"
              className="w-full bg-surface-950 border border-surface-800 rounded-xl px-3 py-2 text-surface-200 focus:outline-none focus:border-brand-500 font-mono"
            />
          </div>

          {/* Retrieval Top-K */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-surface-300">
              <span>Top-K Passages Retrieved</span>
              <span className="font-mono text-emerald-400">{formData.top_k || 5} passages</span>
            </div>
            <input
              type="range"
              min="2"
              max="15"
              value={formData.top_k || 5}
              onChange={(e) => setFormData({ ...formData, top_k: parseInt(e.target.value) })}
              className="w-full accent-emerald-500 bg-surface-800 h-1.5 rounded-lg cursor-pointer"
            />
          </div>

          {/* Infrastructure Health Status */}
          <div className="p-3.5 rounded-xl bg-surface-950/60 border border-surface-800/80 space-y-2">
            <div className="flex items-center space-x-1.5 text-surface-300 font-medium">
              <Database className="w-3.5 h-3.5 text-emerald-400" />
              <span>Storage Engines Active</span>
            </div>
            <div className="grid grid-cols-3 gap-2 font-mono text-[10px] text-surface-400 pt-1">
              <div>
                <span className="text-surface-500 block">DATABASE</span>
                <span className="text-surface-200">SQLite WAL</span>
              </div>
              <div>
                <span className="text-surface-500 block">VECTOR STORE</span>
                <span className="text-surface-200">Qdrant Store</span>
              </div>
              <div>
                <span className="text-surface-500 block">EMBEDDINGS</span>
                <span className="text-surface-200">384d MiniLM</span>
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="pt-2 flex items-center justify-between border-t border-surface-800">
            {savedSuccess ? (
              <span className="text-emerald-400 font-mono flex items-center space-x-1">
                <Check className="w-3.5 h-3.5" />
                <span>Preferences updated!</span>
              </span>
            ) : <span />}

            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl bg-surface-800 hover:bg-surface-750 text-surface-300 font-medium transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSaving}
                className="px-5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-surface-950 font-semibold transition shadow-md shadow-emerald-500/10 disabled:opacity-50"
              >
                {isSaving ? 'Saving...' : 'Save Settings'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
