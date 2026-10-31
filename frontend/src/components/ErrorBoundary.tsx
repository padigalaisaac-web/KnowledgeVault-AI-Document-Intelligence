import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Trash2 } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error caught by KnowledgeVault ErrorBoundary:', error, errorInfo);
    this.setState({ error, errorInfo });
  }

  private handleResetCache = () => {
    try {
      localStorage.clear();
      sessionStorage.clear();
      if ('caches' in window) {
        caches.keys().then((names) => {
          for (const name of names) caches.delete(name);
        });
      }
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.getRegistrations().then((registrations) => {
          for (const reg of registrations) reg.unregister();
        });
      }
    } catch (e) {
      console.warn('Error during cache cleanup:', e);
    }
    window.location.reload();
  };

  private handleReload = () => {
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen w-screen bg-surface-950 text-surface-100 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-surface-900 border border-surface-800 rounded-2xl p-6 shadow-2xl space-y-5 text-center">
            <div className="w-12 h-12 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center mx-auto">
              <AlertTriangle className="w-6 h-6" />
            </div>

            <div className="space-y-1">
              <h2 className="text-base font-semibold text-surface-100">Application Initialization Warning</h2>
              <p className="text-xs text-surface-400">
                KnowledgeVault encountered an unexpected state loading the workspace interface.
              </p>
            </div>

            {this.state.error && (
              <div className="p-3 bg-surface-950 border border-surface-800/80 rounded-xl text-left">
                <p className="text-[11px] font-mono text-rose-300 break-words">
                  {this.state.error.message || String(this.state.error)}
                </p>
              </div>
            )}

            <div className="flex flex-col sm:flex-row items-center justify-center gap-2 pt-2">
              <button
                onClick={this.handleReload}
                className="w-full sm:w-auto px-4 py-2 rounded-xl bg-surface-800 hover:bg-surface-700 text-surface-200 text-xs font-medium transition flex items-center justify-center space-x-1.5"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Reload</span>
              </button>

              <button
                onClick={this.handleResetCache}
                className="w-full sm:w-auto px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-surface-950 text-xs font-semibold transition flex items-center justify-center space-x-1.5 shadow-md shadow-emerald-500/10"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Reset Cache & Reopen</span>
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
