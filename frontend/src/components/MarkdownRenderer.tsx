import React, { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

// Configuration des renderers personnalisés
const renderers = {
  // Rendu Mermaid pour les diagrammes
  code: ({ node, className, children, ...props }: any) => {
    const match = /language-mermaid/.exec(className || '');
    
    if (match) {
      return (
        <MermaidDiagram code={String(children).replace(/\n$/, '')} />
      );
    }
    
    // Rendu pour les autres blocs de code
    return (
      <pre className="bg-gray-900 rounded-lg p-4 overflow-x-auto my-4">
        <code className={className} {...props}>
          {children}
        </code>
      </pre>
    );
  },
};

// Composant pour rendre les diagrammes Mermaid
const MermaidDiagram: React.FC<{ code: string }> = ({ code }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    const renderDiagram = async () => {
      if (!containerRef.current || !code) return;
      
      // Dynamically load Mermaid
      if (!(window as any).mermaid) {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js';
        script.onload = () => initMermaid();
        document.head.appendChild(script);
      } else {
        initMermaid();
      }
    };
    
    const initMermaid = async () => {
      const mermaid = (window as any).mermaid;
      if (!mermaid || !containerRef.current) return;
      
      try {
        mermaid.initialize({
          startOnLoad: false,
          theme: 'default',
          securityLevel: 'loose',
          fontFamily: 'Inter, sans-serif',
        });
        
        const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`;
        const { svg } = await mermaid.render(id, code);
        
        if (containerRef.current) {
          containerRef.current.innerHTML = svg;
        }
      } catch (error) {
        console.error('Mermaid rendering error:', error);
        if (containerRef.current) {
          containerRef.current.innerHTML = `
            <div class="bg-red-50 border border-red-200 rounded-lg p-4">
              <p class="text-red-600 font-medium">Erreur de rendu du diagramme</p>
              <pre class="text-xs text-red-500 mt-2 overflow-x-auto">${code}</pre>
            </div>
          `;
        }
      }
    };
    
    renderDiagram();
  }, [code]);
  
  return (
    <div className="my-4 p-4 bg-white border border-gray-200 rounded-lg overflow-x-auto">
      <div ref={containerRef} className="flex justify-center" />
    </div>
  );
};

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ 
  content, 
  className = '' 
}) => {
  return (
    <div className={`prose prose-sm max-w-none ${className}`}>
      <ReactMarkdown components={renderers as any}>
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;