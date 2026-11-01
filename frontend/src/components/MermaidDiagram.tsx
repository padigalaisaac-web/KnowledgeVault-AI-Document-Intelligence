import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';
import { Copy, Check, GitFork, Maximize2, Minimize2 } from 'lucide-react';

interface MermaidDiagramProps {
  chart: string;
}

// Global mermaid initialization flag
let isMermaidInitialized = false;

function initMermaid() {
  if (!isMermaidInitialized && typeof window !== 'undefined') {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      themeVariables: {
        darkMode: true,
        background: '#0a0f1d',
        primaryColor: '#059669', // emerald-600
        primaryTextColor: '#f3f4f6',
        primaryBorderColor: '#34d399', // emerald-400
        lineColor: '#6ee7b7', // emerald-300
        secondaryColor: '#1e293b',
        tertiaryColor: '#0f172a',
        fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif',
        fontSize: '12px',
        nodeBorder: '#10b981',
        mainBkg: '#111827',
        clusterBkg: '#0b1329',
        clusterBorder: '#1e293b',
      },
      securityLevel: 'loose',
      fontFamily: 'Inter, system-ui, sans-serif',
    });
    isMermaidInitialized = true;
  }
}

export const MermaidDiagram: React.FC<MermaidDiagramProps> = ({ chart }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svgContent, setSvgContent] = useState<string>('');
  const [hasError, setHasError] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    initMermaid();

    let isMounted = true;
    const cleanChart = chart.trim();

    if (!cleanChart) return;

    const renderChart = async () => {
      const uniqueId = `mermaid-${Math.random().toString(36).substring(2, 9)}`;
      try {
        setHasError(false);
        const { svg } = await mermaid.render(uniqueId, cleanChart);
        if (isMounted) {
          setSvgContent(svg);
        }
      } catch (err) {
        console.warn('Failed to render Mermaid diagram:', err);
        if (isMounted) {
          setHasError(true);
        }
      }
    };

    renderChart();

    return () => {
      isMounted = false;
    };
  }, [chart]);

  const handleCopy = () => {
    navigator.clipboard.writeText(chart.trim());
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  // Detect diagram type for header badge
  const firstLine = chart.trim().split('\n')[0].trim().toLowerCase();
  let diagramType = 'Diagram';
  if (firstLine.includes('flowchart') || firstLine.includes('graph')) diagramType = 'Flowchart & Process';
  else if (firstLine.includes('sequencediagram')) diagramType = 'Sequence Architecture';
  else if (firstLine.includes('classdiagram')) diagramType = 'Class & Structural Model';
  else if (firstLine.includes('statediagram')) diagramType = 'State Transitions';
  else if (firstLine.includes('erdiagram')) diagramType = 'Entity Relationship';
  else if (firstLine.includes('mindmap')) diagramType = 'Conceptual Mindmap';
  else if (firstLine.includes('pie')) diagramType = 'Distribution Chart';

  if (hasError) {
    return (
      <div className="my-3 rounded-xl border border-surface-800 bg-surface-950/70 p-3 text-xs font-mono text-surface-400">
        <div className="flex items-center justify-between pb-2 border-b border-surface-800/60 mb-2">
          <span className="text-[10px] uppercase text-surface-500 font-semibold tracking-wider flex items-center gap-1.5">
            <GitFork className="w-3.5 h-3.5 text-amber-400" />
            Diagram Specification
          </span>
          <button
            onClick={handleCopy}
            className="text-[10px] text-surface-400 hover:text-surface-100 flex items-center gap-1"
          >
            {isCopied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            <span>{isCopied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
        <pre className="overflow-x-auto whitespace-pre p-2 text-surface-300">{chart}</pre>
      </div>
    );
  }

  return (
    <div className={`my-4 rounded-2xl border border-surface-800/80 bg-surface-950/90 shadow-xl overflow-hidden transition-all ${isExpanded ? 'p-2' : ''}`}>
      {/* Header Bar */}
      <div className="px-4 py-2.5 bg-surface-900/80 border-b border-surface-800/70 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <GitFork className="w-3.5 h-3.5" />
          </div>
          <div>
            <span className="text-xs font-semibold text-surface-200">
              {diagramType}
            </span>
            <span className="ml-2 text-[10px] font-mono px-1.5 py-0.5 rounded bg-surface-800 text-emerald-400 border border-emerald-500/20">
              Interactive
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-1.5">
          <button
            onClick={handleCopy}
            className="p-1.5 rounded-lg text-surface-400 hover:text-surface-100 hover:bg-surface-800 transition"
            title="Copy Diagram Definition"
          >
            {isCopied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 rounded-lg text-surface-400 hover:text-surface-100 hover:bg-surface-800 transition"
            title={isExpanded ? 'Collapse Diagram' : 'Expand Diagram'}
          >
            {isExpanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* SVG Canvas */}
      <div 
        ref={containerRef}
        className={`p-4 overflow-x-auto flex justify-center items-center bg-gradient-to-b from-surface-950/80 to-surface-950 ${
          isExpanded ? 'min-h-[420px]' : 'max-h-[380px]'
        }`}
        dangerouslySetInnerHTML={{ __html: svgContent }}
      />
    </div>
  );
};
