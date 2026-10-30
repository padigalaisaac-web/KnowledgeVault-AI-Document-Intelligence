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
  BookOpen
} from 'lucide-react';
import { ResearchView } from './components/ResearchView';
import { DocumentVaultView } from './components/DocumentVaultView';
import { BenchmarksView } from './components/BenchmarksView';
import { SourceDrawer } from './components/SourceDrawer';
import { SettingsModal } from './components/SettingsModal';
import { DocumentItem, Collection, Conversation, SystemSettings, HealthStatus, CitationItem } from './types';
import { api } from './services/api';

export function App() {
  const [activeView, setActiveView] = useState<'research' | 'vault' | 'benchmarks'>('research');
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(null);
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [selectedCitation, setSelectedCitation] = useState<CitationItem | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const refreshAll = async () => {
    try {
      const [h, docs, colls, convs, s] = await Promise.all([
        api.getHealth().catch(() => null),
        api.getDocuments().catch(() => []),
        api.getCollections().catch(() => []),
        api.getConversations().catch(() => []),
        api.getSettings().catch(() => null),
      ]);
      if (h) setHealth(h);
      setDocuments(docs);
      setCollections(colls);
      setConversations(convs);
      if (s) setSettings(s);
    } catch (err) {
      console.error('Error refreshing workspace state:', err);
    }
  };

  useEffect(() => {
    refreshAll();
    const interval = setInterval(refreshAll, 15000);
    return () => clearInterval(interval);
  }, []);

  const isHealthy = health?.status === 'healthy';

  return (
    <div className="min-h-screen bg-surface-950 text-surface-100 flex flex-col font-sans selection:bg-emerald-500/20 selection:text-emerald-300">
      {/* Sleek Top Navigation Header */}
      <header className="h-14 border-b border-surface-800 bg-surface-900/80 backdrop-blur-md px-4 md:px-6 flex items-center justify-between sticky top-0 z-40">
        {/* Left: App Logo */}
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-surface-800 border border-surface-700 flex items-center justify-center text-emerald-400 font-bold text-sm shadow-sm">
            KV
          </div>
          <div className="flex items-center space-x-2">
            <h1 className="font-semibold text-surface-100 text-sm tracking-tight">
              KnowledgeVault AI
            </h1>
            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-surface-800 text-emerald-400 border border-emerald-500/20">
              v1.0
            </span>
          </div>
        </div>

        {/* Center: Clean View Switcher */}
        <nav className="flex items-center space-x-1 bg-surface-950/80 border border-surface-800 p-1 rounded-xl text-xs font-medium">
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
        <div className="flex items-center space-x-3">
          <div className="hidden sm:flex items-center space-x-2 bg-surface-950/60 border border-surface-800 px-2.5 py-1 rounded-full text-xs font-mono">
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
      <main className="flex-1 flex overflow-hidden">
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

      {/* Slide-over Source Excerpt Drawer */}
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
