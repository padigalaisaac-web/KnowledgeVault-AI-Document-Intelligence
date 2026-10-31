import React, { useState, useEffect } from 'react';
import {
  MessageSquare,
  FolderArchive,
  BarChart3,
  Sliders,
  HardDrive,
  Cpu,
  Layers,
  Sparkles,
  BookOpen,
  Menu,
  X
} from 'lucide-react';
import { ResearchView } from './components/ResearchView';
import { DocumentVaultView } from './components/DocumentVaultView';
import { BenchmarksView } from './components/BenchmarksView';
import { SourceDrawer } from './components/SourceDrawer';
import { SettingsModal } from './components/SettingsModal';
import { DocumentItem, Collection, Conversation, SystemSettings, HealthStatus, CitationItem } from './types';
import { api } from './services/api';

function loadLocalArray<T>(key: string): T[] {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function loadLocalObject<T>(key: string, defaultValue: T): T {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return defaultValue;
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === 'object' ? parsed : defaultValue;
  } catch {
    return defaultValue;
  }
}

function saveLocal<T>(key: string, value: T): void {
  try {
    if (value === null || value === undefined) {
      localStorage.removeItem(key);
    } else {
      localStorage.setItem(key, JSON.stringify(value));
    }
  } catch (e) {
    console.warn('Failed to save state to localStorage:', e);
  }
}

export function App() {
  const [activeView, setActiveView] = useState<'research' | 'vault' | 'benchmarks'>(() => {
    try {
      const saved = localStorage.getItem('kv_active_view');
      if (saved === 'research' || saved === 'vault' || saved === 'benchmarks') {
        return saved;
      }
    } catch {}
    return 'research';
  });
  const [documents, setDocuments] = useState<DocumentItem[]>(() => loadLocalArray('kv_documents'));
  const [collections, setCollections] = useState<Collection[]>(() => loadLocalArray('kv_collections'));
  const [conversations, setConversations] = useState<Conversation[]>(() => loadLocalArray('kv_conversations'));
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(() => loadLocalObject('kv_active_conv', null));
  const [settings, setSettings] = useState<SystemSettings | null>(() => loadLocalObject('kv_settings', null));
  const [health, setHealth] = useState<HealthStatus | null>(() => loadLocalObject('kv_health', null));
  const [selectedCitation, setSelectedCitation] = useState<CitationItem | null>(() => loadLocalObject('kv_selected_citation', null));
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isMobileDrawerOpen, setIsMobileDrawerOpen] = useState(false);

  // Sync state changes to localStorage for instant hydration across reloads & preview details
  useEffect(() => {
    try {
      localStorage.setItem('kv_active_view', activeView);
    } catch {}
  }, [activeView]);

  useEffect(() => {
    saveLocal('kv_documents', documents);
  }, [documents]);

  useEffect(() => {
    saveLocal('kv_collections', collections);
  }, [collections]);

  useEffect(() => {
    saveLocal('kv_conversations', conversations);
  }, [conversations]);

  useEffect(() => {
    saveLocal('kv_active_conv', activeConversation);
  }, [activeConversation]);

  useEffect(() => {
    saveLocal('kv_selected_citation', selectedCitation);
  }, [selectedCitation]);

  useEffect(() => {
    if (settings) saveLocal('kv_settings', settings);
  }, [settings]);

  useEffect(() => {
    if (health) saveLocal('kv_health', health);
  }, [health]);

  const refreshAll = async () => {
    try {
      const [h, docs, colls, convs, s] = await Promise.all([
        api.getHealth().catch(() => null),
        api.getDocuments().catch(() => null),
        api.getCollections().catch(() => null),
        api.getConversations().catch(() => null),
        api.getSettings().catch(() => null),
      ]);
      if (h) setHealth(h);
      if (Array.isArray(docs)) setDocuments(docs);
      if (Array.isArray(colls)) setCollections(colls);
      if (Array.isArray(convs)) {
        setConversations(convs);
        // Keep active conversation reference fresh
        setActiveConversation((prev) => {
          if (!prev) return null;
          const match = convs.find((c: Conversation) => c && c.id === prev.id);
          return match || prev;
        });
      }
      if (s) setSettings(s);
    } catch (err) {
      console.error('Error refreshing workspace state:', err);
    }
  };

  useEffect(() => {
    refreshAll();
    const interval = setInterval(() => {
      if (document.visibilityState === 'visible') {
        refreshAll();
      }
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const isHealthy = health?.status === 'healthy';

  return (
    <div className="h-screen w-screen overflow-hidden bg-surface-950 text-surface-100 flex flex-col font-sans selection:bg-emerald-500/20 selection:text-emerald-300">
      {/* Sleek Top Navigation Header */}
      <header className="h-14 border-b border-surface-800 bg-surface-900/80 backdrop-blur-md px-3 md:px-6 flex items-center justify-between sticky top-0 z-40 shrink-0">
        {/* Left: App Logo & Mobile Menu Toggle */}
        <div className="flex items-center space-x-2.5">
          {activeView === 'research' && (
            <button
              onClick={() => setIsMobileDrawerOpen(!isMobileDrawerOpen)}
              className="p-1.5 rounded-lg text-surface-400 hover:text-surface-100 hover:bg-surface-800 md:hidden"
              aria-label="Toggle threads drawer"
            >
              {isMobileDrawerOpen ? <X className="w-5 h-5 text-emerald-400" /> : <Menu className="w-5 h-5" />}
            </button>
          )}

          <div className="w-8 h-8 rounded-lg bg-surface-800 border border-surface-700 flex items-center justify-center text-emerald-400 font-bold text-sm shadow-sm">
            KV
          </div>
          <div className="flex items-center space-x-2">
            <h1 className="font-semibold text-surface-100 text-sm tracking-tight truncate max-w-[140px] sm:max-w-none">
              KnowledgeVault AI
            </h1>
            <span className="hidden sm:inline-block text-[10px] font-mono px-1.5 py-0.2 rounded bg-surface-800 text-emerald-400 border border-emerald-500/20">
              v1.0
            </span>
          </div>
        </div>

        {/* Center: Desktop View Switcher */}
        <nav className="hidden md:flex items-center space-x-1 bg-surface-950/80 border border-surface-800 p-1 rounded-xl text-xs font-medium">
          <button
            onClick={() => setActiveView('research')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg transition-all ${
              activeView === 'research'
                ? 'bg-surface-800 text-emerald-400 font-semibold shadow-sm'
                : 'text-surface-400 hover:text-surface-200'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Research</span>
          </button>

          <button
            onClick={() => setActiveView('vault')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg transition-all ${
              activeView === 'vault'
                ? 'bg-surface-800 text-emerald-400 font-semibold shadow-sm'
                : 'text-surface-400 hover:text-surface-200'
            }`}
          >
            <FolderArchive className="w-3.5 h-3.5" />
            <span>Document Vault</span>
            {documents.length > 0 && (
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded-full bg-surface-900 text-surface-300">
                {documents.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveView('benchmarks')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg transition-all ${
              activeView === 'benchmarks'
                ? 'bg-surface-800 text-emerald-400 font-semibold shadow-sm'
                : 'text-surface-400 hover:text-surface-200'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Benchmarks</span>
          </button>
        </nav>

        {/* Right: Telemetry & Settings */}
        <div className="flex items-center space-x-2">
          <div className="hidden lg:flex items-center space-x-2 bg-surface-950/60 border border-surface-800 px-2.5 py-1 rounded-full text-xs font-mono">
            <span className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-emerald-400' : 'bg-amber-400'}`} />
            <span className="text-surface-300">{isHealthy ? 'Online' : 'Degraded'}</span>
            <span className="text-surface-700">•</span>
            <span className="text-surface-400">{health?.indexed_vector_count ?? 0} vectors</span>
          </div>

          <button
            onClick={() => setIsSettingsOpen(true)}
            className="p-2 rounded-xl bg-surface-800 hover:bg-surface-700 text-surface-300 hover:text-surface-100 transition border border-surface-700"
            title="System Settings"
          >
            <Sliders className="w-3.5 h-3.5" />
          </button>
        </div>
      </header>

      {/* Main Workspace Stage */}
      <main className="flex-1 flex overflow-hidden relative">
        {activeView === 'research' && (
          <ResearchView
            conversations={conversations}
            collections={collections}
            documents={documents}
            activeConversation={activeConversation}
            setActiveConversation={setActiveConversation}
            onRefreshConversations={refreshAll}
            onSelectCitation={(cit) => setSelectedCitation(cit)}
            onNavigateToDocs={() => setActiveView('vault')}
            isMobileDrawerOpen={isMobileDrawerOpen}
            onCloseMobileDrawer={() => setIsMobileDrawerOpen(false)}
          />
        )}

        {activeView === 'vault' && (
          <DocumentVaultView
            documents={documents}
            collections={collections}
            onRefresh={refreshAll}
          />
        )}

        {activeView === 'benchmarks' && (
          <BenchmarksView />
        )}
      </main>

      {/* Mobile Bottom Navigation Bar (Visible only on mobile screens) */}
      <nav className="md:hidden flex items-center justify-around h-16 bg-surface-900/95 border-t border-surface-800 backdrop-blur-lg px-2 z-30 shrink-0">
        <button
          onClick={() => { setActiveView('research'); setIsMobileDrawerOpen(false); }}
          className={`flex flex-col items-center justify-center flex-1 py-1 transition ${
            activeView === 'research' ? 'text-emerald-400 font-semibold' : 'text-surface-400'
          }`}
        >
          <MessageSquare className="w-5 h-5 mb-0.5" />
          <span className="text-[10px]">Research</span>
        </button>

        <button
          onClick={() => { setActiveView('vault'); setIsMobileDrawerOpen(false); }}
          className={`flex flex-col items-center justify-center flex-1 py-1 transition ${
            activeView === 'vault' ? 'text-emerald-400 font-semibold' : 'text-surface-400'
          }`}
        >
          <div className="relative">
            <FolderArchive className="w-5 h-5 mb-0.5" />
            {documents.length > 0 && (
              <span className="absolute -top-1 -right-2 px-1 text-[9px] font-mono rounded-full bg-emerald-500 text-surface-950 font-bold">
                {documents.length}
              </span>
            )}
          </div>
          <span className="text-[10px]">Vault</span>
        </button>

        <button
          onClick={() => { setActiveView('benchmarks'); setIsMobileDrawerOpen(false); }}
          className={`flex flex-col items-center justify-center flex-1 py-1 transition ${
            activeView === 'benchmarks' ? 'text-emerald-400 font-semibold' : 'text-surface-400'
          }`}
        >
          <BarChart3 className="w-5 h-5 mb-0.5" />
          <span className="text-[10px]">Benchmarks</span>
        </button>
      </nav>

      {/* Slide-over Source Excerpt Drawer / Bottom Sheet on Mobile */}
      <SourceDrawer
        citation={selectedCitation}
        onClose={() => setSelectedCitation(null)}
      />

      {/* System Settings Dialog */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        settings={settings}
        health={health}
        onRefresh={refreshAll}
      />
    </div>
  );
}

export default App;
