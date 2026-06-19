import React, { useState } from 'react';
import { History, RotateCcw, Clock, ChevronDown, ChevronRight } from 'lucide-react';
import { Button } from './ui/Button';

interface Version {
  id: number;
  version: number;
  content: string;
  created_at: string;
  created_by?: string;
  change_summary?: string;
}

interface DocumentHistoryProps {
  versions: Version[];
  currentVersion: number;
  onRestore: (version: Version) => void;
  isRestoring?: boolean;
}

export const DocumentHistory: React.FC<DocumentHistoryProps> = ({
  versions,
  currentVersion,
  onRestore,
  isRestoring = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedVersion, setSelectedVersion] = useState<Version | null>(null);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleRestore = (version: Version) => {
    if (confirm(`Voulez-vous restaurer la version ${version.version} ?`)) {
      onRestore(version);
    }
  };

  const getDiff = (v1: string, v2: string): { added: number; removed: number } => {
    const lines1 = v1.split('\n');
    const lines2 = v2.split('\n');
    
    const added = lines2.length - lines1.length;
    const removed = added < 0 ? Math.abs(added) : 0;
    
    return { added: Math.max(0, added), removed };
  };

  return (
    <div className="border border-gray-200 rounded-lg bg-white">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <History className="w-5 h-5 text-gray-500" />
          <span className="font-medium text-gray-900">Historique des versions</span>
          <span className="text-sm text-gray-500">({versions.length} versions)</span>
        </div>
        {isExpanded ? (
          <ChevronDown className="w-5 h-5 text-gray-400" />
        ) : (
          <ChevronRight className="w-5 h-5 text-gray-400" />
        )}
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-gray-200">
          {versions.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              Aucune version disponible
            </div>
          ) : (
            <div className="max-h-96 overflow-y-auto">
              {versions
                .sort((a, b) => b.version - a.version)
                .map((version, index) => {
                  const isCurrent = version.version === currentVersion;
                  const prevVersion = versions[index + 1];
                  const diff = prevVersion ? getDiff(prevVersion.content, version.content) : null;

                  return (
                    <div
                      key={version.id}
                      className={`px-4 py-3 border-b border-gray-100 last:border-b-0 ${
                        isCurrent ? 'bg-primary-50' : 'hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-gray-900">
                              Version {version.version}
                            </span>
                            {isCurrent && (
                              <span className="px-2 py-0.5 bg-primary-100 text-primary-700 text-xs rounded-full">
                                Actuelle
                              </span>
                            )}
                          </div>
                          
                          <div className="flex items-center gap-2 mt-1 text-sm text-gray-500">
                            <Clock className="w-3 h-3" />
                            <span>{formatDate(version.created_at)}</span>
                            {diff && (
                              <span className="text-xs">
                                <span className="text-green-600">+{diff.added}</span>
                                {' / '}
                                <span className="text-red-600">-{diff.removed}</span>
                              </span>
                            )}
                          </div>

                          {version.change_summary && (
                            <p className="text-sm text-gray-600 mt-1">
                              {version.change_summary}
                            </p>
                          )}
                        </div>

                        {!isCurrent && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRestore(version)}
                            isLoading={isRestoring}
                          >
                            <RotateCcw className="w-4 h-4 mr-1" />
                            Restaurer
                          </Button>
                        )}
                      </div>

                      {/* Preview comparison */}
                      {selectedVersion?.id === version.id && (
                        <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                          <h4 className="text-sm font-medium mb-2">Aperçu</h4>
                          <pre className="text-xs text-gray-600 overflow-x-auto max-h-40">
                            {version.content.substring(0, 500)}
                            {version.content.length > 500 && '...'}
                          </pre>
                        </div>
                      )}
                    </div>
                  );
                })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DocumentHistory;