import React from 'react';
import { marked } from 'marked';
import { MermaidDiagram } from './MermaidDiagram';
import { CitationItem } from '../types';
import { Bookmark, FileText } from 'lucide-react';

interface ExplainableMessageRendererProps {
  content: string;
  sources?: CitationItem[];
  onSelectCitation?: (cit: CitationItem) => void;
}

interface ContentSegment {
  type: 'markdown' | 'mermaid' | 'code';
  content: string;
  language?: string;
}

export const ExplainableMessageRenderer: React.FC<ExplainableMessageRendererProps> = ({
  content,
  sources = [],
  onSelectCitation,
}) => {
  // Parse content into markdown, code blocks, and mermaid diagrams
  const segments: ContentSegment[] = React.useMemo(() => {
    const list: ContentSegment[] = [];
    // Regex matching ```language \n code ```
    const codeBlockRegex = /```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g;
    let lastIndex = 0;
    let match: RegExpExecArray | null;

    while ((match = codeBlockRegex.exec(content)) !== null) {
      const matchIndex = match.index;
      if (matchIndex > lastIndex) {
        list.push({
          type: 'markdown',
          content: content.substring(lastIndex, matchIndex),
        });
      }

      const lang = (match[1] || '').trim().toLowerCase();
      const code = match[2];

      if (lang === 'mermaid') {
        list.push({
          type: 'mermaid',
          content: code,
          language: 'mermaid',
        });
      } else {
        list.push({
          type: 'code',
          content: code,
          language: lang || 'text',
        });
      }

      lastIndex = matchIndex + match[0].length;
    }

    if (lastIndex < content.length) {
      list.push({
        type: 'markdown',
        content: content.substring(lastIndex),
      });
    }

    return list;
  }, [content]);

  // Convert markdown text to HTML while replacing citation tags [1], [2] with clickable badges
  const renderMarkdownWithCitations = (markdownText: string) => {
    // Configure marked options
    const rawHtml = marked.parse(markdownText, {
      gfm: true,
      breaks: true,
    }) as string;

    // Enhance citation footnotes [1], [2], etc.
    // Replace [1] with interactive span
    const enhancedHtml = rawHtml.replace(/\[(\d+)\]/g, (match, num) => {
      return `<button data-citation-idx="${num}" class="citation-pill inline-flex items-center px-1.5 py-0.2 mx-0.5 rounded text-[11px] font-mono font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/30 hover:text-emerald-300 transition cursor-pointer select-none align-baseline">[${num}]</button>`;
    });

    return (
      <div
        className="prose prose-invert prose-sm max-w-none space-y-3 leading-relaxed text-surface-200
          prose-headings:text-surface-100 prose-headings:font-semibold prose-headings:tracking-tight
          prose-h1:text-base prose-h2:text-sm prose-h3:text-xs prose-h3:text-emerald-400 prose-h3:font-mono prose-h3:uppercase
          prose-p:my-2 prose-p:leading-relaxed
          prose-strong:text-surface-100 prose-strong:font-semibold prose-strong:text-emerald-300
          prose-ul:list-disc prose-ul:pl-5 prose-ul:my-2 prose-li:my-1
          prose-ol:list-decimal prose-ol:pl-5 prose-ol:my-2
          prose-blockquote:border-l-2 prose-blockquote:border-emerald-500 prose-blockquote:bg-surface-950/60 prose-blockquote:p-3 prose-blockquote:rounded-r-xl prose-blockquote:italic
          prose-table:border-collapse prose-table:w-full prose-table:my-3
          prose-th:border prose-th:border-surface-800 prose-th:p-2 prose-th:bg-surface-950 prose-th:text-surface-300 prose-th:font-mono prose-th:text-[11px]
          prose-td:border prose-td:border-surface-800 prose-td:p-2 prose-td:text-surface-300 prose-td:text-xs"
        dangerouslySetInnerHTML={{ __html: enhancedHtml }}
        onClick={(e) => {
          const target = (e.target as HTMLElement).closest('[data-citation-idx]');
          if (target && onSelectCitation) {
            const idxStr = target.getAttribute('data-citation-idx');
            if (idxStr) {
              const num = parseInt(idxStr, 10);
              const matchedCit = sources.find((s) => s.citation_id === `[${num}]` || s.citation_id === `${num}`);
              if (matchedCit) {
                onSelectCitation(matchedCit);
              } else if (sources[num - 1]) {
                onSelectCitation(sources[num - 1]);
              }
            }
          }
        }}
      />
    );
  };

  return (
    <div className="space-y-3">
      {segments.map((seg, idx) => {
        if (seg.type === 'mermaid') {
          return <MermaidDiagram key={idx} chart={seg.content} />;
        }

        if (seg.type === 'code') {
          return (
            <div key={idx} className="my-3 rounded-xl border border-surface-800 bg-surface-950 overflow-hidden font-mono text-xs">
              <div className="px-3.5 py-1.5 bg-surface-900 border-b border-surface-800 text-[10px] uppercase font-bold text-surface-400 flex items-center justify-between">
                <span>{seg.language}</span>
                <button
                  onClick={() => navigator.clipboard.writeText(seg.content)}
                  className="hover:text-emerald-400 transition"
                >
                  Copy
                </button>
              </div>
              <pre className="p-3.5 overflow-x-auto text-surface-200 whitespace-pre leading-relaxed">
                {seg.content}
              </pre>
            </div>
          );
        }

        return <React.Fragment key={idx}>{renderMarkdownWithCitations(seg.content)}</React.Fragment>;
      })}
    </div>
  );
};
