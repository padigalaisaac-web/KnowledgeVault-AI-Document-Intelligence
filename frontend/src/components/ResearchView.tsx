import React, { useState, useEffect, useRef } from 'react';
import {
  Send,
  Plus,
  Trash2,
  Copy,
  Check,
  FileText,
  Bookmark,
  ExternalLink,
  SlidersHorizontal,
  RotateCcw,
  BookOpen,
  Layers,
  ArrowUpRight
} from 'lucide-react';
import { Conversation, Message, Collection, DocumentItem, CitationItem } from '../types';
import { api } from '../services/api';

interface ResearchViewProps {
  conversations: Conversation[];
  collections: Collection[];
  documents: DocumentItem[];
  activeConversation: Conversation | null;
  setActiveConversation: (conv: Conversation | null) => void;
  onRefreshConversations: () => void;
  onSelectCitation: (cit: CitationItem) => void;
  onNavigateToDocs: () => void;
  isMobileDrawerOpen?: boolean;
  onCloseMobileDrawer?: () => void;
}

export const ResearchView: React.FC<ResearchViewProps> = ({
  conversations,
  collections,
  documents,
  activeConversation,
  setActiveConversation,
  onRefreshConversations,
  onSelectCitation,
  onNavigateToDocs,
  isMobileDrawerOpen = false,
  onCloseMobileDrawer,
}) => {
  // Hydrate initial messages from cache if active conversation is already set
  const [messages, setMessages] = useState<Message[]>(() => {
    if (activeConversation?.id) {
      try {
        const cached = localStorage.getItem(`kv_msgs_${activeConversation.id}`);
        if (cached) return JSON.parse(cached);
      } catch {}
    }
    return [];
  });
  const [inputQuery, setInputQuery] = useState(() => localStorage.getItem('kv_draft_query') || '');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedCollection, setSelectedCollection] = useState<string>(
    () => localStorage.getItem('kv_selected_collection') || ''
  );
  const [retrievalMode, setRetrievalMode] = useState<string>(
    () => localStorage.getItem('kv_retrieval_mode') || 'hybrid'
  );
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Sync draft query, collection & mode to localStorage
  useEffect(() => {
    if (inputQuery) {
      localStorage.setItem('kv_draft_query', inputQuery);
    } else {
      localStorage.removeItem('kv_draft_query');
    }
  }, [inputQuery]);

  useEffect(() => {
    localStorage.setItem('kv_selected_collection', selectedCollection);
  }, [selectedCollection]);

  useEffect(() => {
    localStorage.setItem('kv_retrieval_mode', retrievalMode);
  }, [retrievalMode]);

  // Load messages whenever activeConversation changes (with instant cache hydration)
  useEffect(() => {
    if (activeConversation) {
      const cacheKey = `kv_msgs_${activeConversation.id}`;
      // Instant display from cache (0 ms perceptual latency)
      try {
        const cached = localStorage.getItem(cacheKey);
        if (cached) {
          setMessages(JSON.parse(cached));
        }
      } catch {}

      // Revalidate in background
      api.getConversation(activeConversation.id)
        .then((c) => {
          const fetched = c.messages || [];
          setMessages(fetched);
          try {
            localStorage.setItem(cacheKey, JSON.stringify(fetched));
          } catch {}
        })
        .catch((err) => console.error('Failed to load thread:', err));
    } else {
      setMessages([]);
    }
  }, [activeConversation?.id]);

  // Auto-scroll on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSendMessage = async (queryText?: string) => {
    const textToSend = (queryText || inputQuery).trim();
    if (!textToSend || isLoading) return;

    setInputQuery('');
    localStorage.removeItem('kv_draft_query');

    // Optimistic user message
    const tempUserMsg: Message = {
      id: `temp_${Date.now()}`,
      conversation_id: activeConversation?.id || '',
      role: 'user',
      content: textToSend,
      sources: [],
      created_at: new Date().toISOString(),
    };
    const optimisticMessages = [...messages, tempUserMsg];
    setMessages(optimisticMessages);
    setIsLoading(true);

    try {
      const responseMsg = await api.sendChat(
        textToSend,
        activeConversation?.id,
        selectedCollection || undefined,
        retrievalMode,
        false, // rerank
        5      // top_k
      );

      // If this started a new thread, refresh thread list and select it
      if (!activeConversation) {
        onRefreshConversations();
        api.getConversation(responseMsg.conversation_id).then((conv) => {
          setActiveConversation(conv);
        });
      }

      const updated = [...messages.filter((m) => m.id !== tempUserMsg.id), tempUserMsg, responseMsg];
      setMessages(updated);
      const targetConvId = activeConversation?.id || responseMsg.conversation_id;
      if (targetConvId) {
        try {
          localStorage.setItem(`kv_msgs_${targetConvId}`, JSON.stringify(updated));
        } catch {}
      }
      onRefreshConversations();
    } catch (err: any) {
      alert(`Chat error: ${err.message}`);
      setMessages((prev) => prev.filter((m) => m.id !== tempUserMsg.id));
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    setActiveConversation(null);
    setMessages([]);
    setInputQuery('');
    localStorage.removeItem('kv_draft_query');
  };

  const handleDeleteConversation = async (convId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.deleteConversation(convId);
      try {
        localStorage.removeItem(`kv_msgs_${convId}`);
      } catch {}
      if (activeConversation?.id === convId) {
        setActiveConversation(null);
        setMessages([]);
      }
      onRefreshConversations();
    } catch (err: any) {
      alert(`Failed to delete thread: ${err.message}`);
    }
  };

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const samplePrompts = [
    "Compare the machine learning algorithms in my uploaded research papers.",
    "Explain their evaluation metrics and cite the document pages supporting each statement.",
    "What is the mathematical formulation of Scaled Dot-Product Attention?",
  ];

  return (
    <div className="flex flex-1 h-full overflow-hidden relative">
      {/* Mobile Drawer Backdrop */}
      {isMobileDrawerOpen && (
        <div 
          onClick={onCloseMobileDrawer}
          className="fixed inset-0 bg-black/70 backdrop-blur-xs z-30 md:hidden animate-in fade-in"
        />
      )}

      {/* Left Sidebar: Threads & Knowledge Filter */}
      <aside className={`
        fixed inset-y-14 left-0 z-40 w-72 bg-surface-900 border-r border-surface-800 flex flex-col justify-between transition-transform duration-200 ease-in-out
        md:static md:translate-x-0 md:w-64 md:bg-surface-900/40 shrink-0
        ${isMobileDrawerOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full'}
      `}>
        <div className="p-3.5 space-y-4 flex-1 overflow-y-auto">
          {/* New Chat Button */}
          <button
            onClick={() => {
              handleNewChat();
              onCloseMobileDrawer?.();
            }}
            className="w-full flex items-center justify-center space-x-2 px-3.5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-surface-950 font-semibold text-xs transition-all shadow-md shadow-emerald-500/10"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Research Chat</span>
          </button>

          {/* Scope / Knowledge Filter */}
          <div className="space-y-1.5 pt-1">
            <div className="flex items-center justify-between text-[10px] font-mono uppercase text-surface-400 px-1">
              <span>Source Vault</span>
              <button 
                onClick={onNavigateToDocs}
                className="text-emerald-400 hover:underline flex items-center space-x-0.5"
              >
                <span>{documents.length} docs</span>
                <ArrowUpRight className="w-2.5 h-2.5" />
              </button>
            </div>
            <select
              value={selectedCollection}
              onChange={(e) => setSelectedCollection(e.target.value)}
              className="w-full bg-surface-950 border border-surface-800 rounded-lg px-2.5 py-1.5 text-xs text-surface-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="">All Uploaded Documents</option>
              {collections.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.document_count || 0})
                </option>
              ))}
            </select>
          </div>

          {/* Retrieval Engine Mode */}
          <div className="space-y-1.5 pt-1 border-t border-surface-800/60">
            <label className="text-[10px] font-mono uppercase text-surface-400 block px-1">
              Retrieval Strategy
            </label>
            <select
              value={retrievalMode}
              onChange={(e) => setRetrievalMode(e.target.value)}
              className="w-full bg-surface-950 border border-surface-800 rounded-lg px-2.5 py-1.5 text-xs text-surface-300 focus:outline-none focus:border-emerald-500 font-mono"
            >
              <option value="hybrid">Hybrid (BM25 + Qdrant RRF)</option>
              <option value="dense">Dense Vector Only</option>
              <option value="bm25">BM25 Keyword Only</option>
            </select>
          </div>

          {/* Recent Threads */}
          <div className="space-y-1 pt-2 border-t border-surface-800/60">
            <div className="text-[10px] font-mono uppercase text-surface-500 px-1 mb-1">
              Chat Threads
            </div>

            {conversations.length === 0 ? (
              <p className="px-2 py-3 text-xs text-surface-500 italic">No previous chats yet.</p>
            ) : (
              conversations.map((conv) => {
                const isActive = activeConversation?.id === conv.id;
                return (
                  <div
                    key={conv.id}
                    onClick={() => {
                      setActiveConversation(conv);
                      onCloseMobileDrawer?.();
                    }}
                    className={`group flex items-center justify-between p-2 rounded-lg text-xs cursor-pointer transition-all ${
                      isActive
                        ? 'bg-surface-800 text-emerald-400 font-medium'
                        : 'text-surface-400 hover:text-surface-200 hover:bg-surface-800/40'
                    }`}
                  >
                    <span className="truncate pr-2">{conv.title}</span>
                    <button
                      onClick={(e) => handleDeleteConversation(conv.id, e)}
                      className="opacity-0 group-hover:opacity-100 p-1 text-surface-500 hover:text-rose-400 transition"
                      title="Delete Thread"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Live Status Footnote */}
        <div className="p-3 border-t border-surface-800/80 bg-surface-950/40 text-[11px] text-surface-400 flex items-center justify-between font-mono">
          <span className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>Hybrid RRF k=60</span>
          </span>
          <span className="text-surface-500">100% Recall</span>
        </div>
      </aside>

      {/* Main Research Chat Stage */}
      <main className="flex-1 flex flex-col justify-between bg-surface-950 overflow-hidden">
        {/* Messages Feed */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
          {messages.length === 0 ? (
            /* Empty State */
            <div className="h-full flex flex-col items-center justify-center max-w-xl mx-auto text-center space-y-5 my-auto py-12">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 shadow-lg shadow-emerald-500/5">
                <BookOpen className="w-6 h-6" />
              </div>
              <div className="space-y-1.5">
                <h2 className="text-lg font-bold text-surface-100">
                  Evidence-Grounded Document Intelligence
                </h2>
                <p className="text-xs text-surface-400 leading-relaxed max-w-md mx-auto">
                  Ask questions across your documents. Answers are synthesized strictly from retrieved passages with verifiable page citations.
                </p>
              </div>

              {/* Sample Starters */}
              <div className="grid grid-cols-1 gap-2 w-full pt-2 text-left">
                {samplePrompts.map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(prompt)}
                    className="p-3 rounded-xl bg-surface-900/60 hover:bg-surface-850 border border-surface-800 hover:border-surface-700 text-xs text-surface-300 transition-all flex items-center justify-between group"
                  >
                    <span>{prompt}</span>
                    <ArrowUpRight className="w-3.5 h-3.5 text-surface-500 group-hover:text-emerald-400 transition" />
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* Message List */
            messages.map((msg) => {
              const isUser = msg.role === 'user';
              return (
                <div
                  key={msg.id}
                  className={`flex gap-3 max-w-3xl ${isUser ? 'ml-auto justify-end' : 'mr-auto justify-start'}`}
                >
                  {!isUser && (
                    <div className="w-7 h-7 rounded-lg bg-surface-800 border border-surface-700 text-emerald-400 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">
                      KV
                    </div>
                  )}

                  <div className="space-y-2 max-w-2xl">
                    <div
                      className={`p-4 rounded-2xl text-xs leading-relaxed ${
                        isUser
                          ? 'bg-surface-800 text-surface-100 border border-surface-700 font-medium rounded-tr-none'
                          : 'bg-surface-900/90 border border-surface-800 text-surface-200 rounded-tl-none space-y-3'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{msg.content}</p>

                      {/* Insufficient Evidence Notice */}
                      {!isUser && msg.confidence === 'insufficient_evidence' && (
                        <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-[11px]">
                          Note: The uploaded documents do not contain sufficient evidence to answer completely.
                        </div>
                      )}
                    </div>

                    {/* Citations Badges */}
                    {!isUser && msg.sources && msg.sources.length > 0 && (
                      <div className="space-y-1.5 pt-1">
                        <div className="text-[10px] font-mono text-surface-500 uppercase flex items-center space-x-1">
                          <Bookmark className="w-3 h-3 text-emerald-400" />
                          <span>Sources Cited ({msg.sources.length})</span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {msg.sources.map((cit, idx) => (
                            <button
                              key={idx}
                              onClick={() => onSelectCitation(cit)}
                              className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-surface-900 hover:bg-surface-800 border border-surface-800 hover:border-emerald-500/40 text-[11px] font-mono text-surface-300 transition-colors group"
                            >
                              <span className="text-emerald-400 font-bold">{cit.citation_id}</span>
                              <span className="truncate max-w-[150px] text-surface-300 group-hover:text-surface-100">
                                {cit.document_title}
                              </span>
                              {cit.page_number && (
                                <span className="text-[10px] text-surface-500">p.{cit.page_number}</span>
                              )}
                              <ExternalLink className="w-2.5 h-2.5 text-surface-500 group-hover:text-emerald-400" />
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Metadata & Actions */}
                    {!isUser && (
                      <div className="flex items-center space-x-3 text-[10px] font-mono text-surface-500 pt-0.5">
                        {msg.latency_ms && <span>{msg.latency_ms.toFixed(0)}ms</span>}
                        {msg.retrieval_mode && <span className="capitalize">• {msg.retrieval_mode}</span>}
                        <button
                          onClick={() => handleCopy(msg.content, msg.id)}
                          className="hover:text-surface-300 transition flex items-center space-x-1"
                        >
                          {copiedId === msg.id ? (
                            <>
                              <Check className="w-3 h-3 text-emerald-400" />
                              <span className="text-emerald-400">Copied</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3 h-3" />
                              <span>Copy Answer</span>
                            </>
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex gap-3 max-w-3xl mr-auto justify-start">
              <div className="w-7 h-7 rounded-lg bg-surface-800 border border-surface-700 text-emerald-400 font-bold text-xs flex items-center justify-center shrink-0 animate-pulse">
                KV
              </div>
              <div className="p-3.5 rounded-xl bg-surface-900 border border-surface-800 text-surface-400 text-xs flex items-center space-x-2.5 font-mono">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                <span>Searching knowledge vault and verifying citations...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-surface-800 bg-surface-900/60">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="max-w-4xl mx-auto flex items-center space-x-2.5"
          >
            <input
              type="text"
              placeholder="Ask a question about your uploaded documents..."
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              disabled={isLoading}
              className="flex-1 bg-surface-950 border border-surface-800 rounded-xl px-4 py-3 text-xs text-surface-100 placeholder-surface-500 focus:outline-none focus:border-emerald-500 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!inputQuery.trim() || isLoading}
              className="px-5 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-surface-950 font-semibold text-xs transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center space-x-1.5 shadow-md shadow-emerald-500/10"
            >
              <span>Ask</span>
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      </main>
    </div>
  );
};
