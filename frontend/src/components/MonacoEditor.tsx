import React, { useState, useCallback } from 'react';
import { Eye, Edit3, Save, RotateCcw } from 'lucide-react';
import { Button } from './ui/Button';
import { MarkdownRenderer } from './MarkdownRenderer';

interface MonacoEditorProps {
  content: string;
  onChange: (content: string) => void;
  onSave: () => void;
  isSaving?: boolean;
  originalContent?: string;
  language?: string;
}

export const MonacoEditor: React.FC<MonacoEditorProps> = ({
  content,
  onChange,
  onSave,
  isSaving = false,
  originalContent,
  language = 'markdown',
}) => {
  const [viewMode, setViewMode] = useState<'edit' | 'preview' | 'split'>('split');
  const [localContent, setLocalContent] = useState(content);
  const [isDirty, setIsDirty] = useState(false);

  // Sync external content changes
  React.useEffect(() => {
    setLocalContent(content);
  }, [content]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newContent = e.target.value;
    setLocalContent(newContent);
    onChange(newContent);
    setIsDirty(newContent !== originalContent);
  }, [onChange, originalContent]);

  const handleReset = useCallback(() => {
    if (originalContent && confirm('Voulez-vous annuler les modifications ?')) {
      setLocalContent(originalContent);
      onChange(originalContent);
      setIsDirty(false);
    }
  }, [originalContent, onChange]);

  const hasChanges = isDirty || localContent !== content;

  return (
    <div className="border border-gray-300 rounded-lg overflow-hidden bg-white">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setViewMode('edit')}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              viewMode === 'edit'
                ? 'bg-primary-100 text-primary-700'
                : 'text-gray-600 hover:bg-gray-200'
            }`}
          >
            <Edit3 className="w-4 h-4 inline mr-1" />
            Éditer
          </button>
          <button
            onClick={() => setViewMode('split')}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              viewMode === 'split'
                ? 'bg-primary-100 text-primary-700'
                : 'text-gray-600 hover:bg-gray-200'
            }`}
          >
            Split
          </button>
          <button
            onClick={() => setViewMode('preview')}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              viewMode === 'preview'
                ? 'bg-primary-100 text-primary-700'
                : 'text-gray-600 hover:bg-gray-200'
            }`}
          >
            <Eye className="w-4 h-4 inline mr-1" />
            Aperçu
          </button>
        </div>

        <div className="flex items-center gap-2">
          {hasChanges && (
            <span className="text-xs text-orange-500 font-medium">
              Modifications non sauvegardées
            </span>
          )}
          {isDirty && (
            <Button variant="ghost" size="sm" onClick={handleReset}>
              <RotateCcw className="w-4 h-4 mr-1" />
              Annuler
            </Button>
          )}
          <Button size="sm" onClick={onSave} isLoading={isSaving} disabled={!hasChanges}>
            <Save className="w-4 h-4 mr-1" />
            Sauvegarder
          </Button>
        </div>
      </div>

      {/* Editor / Preview Area */}
      <div className={`flex ${viewMode === 'split' ? 'divide-x divide-gray-200' : ''}`}>
        {/* Edit Mode */}
        {(viewMode === 'edit' || viewMode === 'split') && (
          <div className={`${viewMode === 'split' ? 'w-1/2' : 'w-full'}`}>
            <textarea
              value={localContent}
              onChange={handleChange}
              className="w-full h-[500px] p-4 font-mono text-sm resize-none focus:outline-none bg-gray-50"
              placeholder="Entrez votre contenu Markdown..."
              spellCheck={false}
            />
          </div>
        )}

        {/* Preview Mode */}
        {(viewMode === 'preview' || viewMode === 'split') && (
          <div className={`${viewMode === 'split' ? 'w-1/2' : 'w-full'} p-4 overflow-y-auto bg-white`}>
            <MarkdownRenderer content={localContent} />
          </div>
        )}
      </div>

      {/* Status Bar */}
      <div className="flex items-center justify-between px-4 py-1.5 bg-gray-100 border-t border-gray-200 text-xs text-gray-500">
        <span>
          {localContent.length} caractères | {localContent.split(/\s+/).filter(Boolean).length} mots
        </span>
        <span>
          Mode: {viewMode === 'edit' ? 'Édition' : viewMode === 'preview' ? 'Aperçu' : 'Split'}
        </span>
      </div>
    </div>
  );
};

export default MonacoEditor;