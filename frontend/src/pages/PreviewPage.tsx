import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, Rocket, Play, Square, ExternalLink,
  Clock, CheckCircle, AlertCircle, Loader2, RefreshCw, Terminal
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import toast from 'react-hot-toast';

interface PreviewInstance {
  id: string;
  project_id: number;
  status: string;
  port: number;
  url?: string;
  created_at: string;
  expires_at: string;
}

const statusConfig = {
  building: { label: 'Construction...', color: 'bg-blue-100 text-blue-700', icon: Loader2 },
  running: { label: 'En cours', color: 'bg-green-100 text-green-700', icon: Play },
  stopped: { label: 'Arrêté', color: 'bg-gray-100 text-gray-700', icon: Square },
  error: { label: 'Erreur', color: 'bg-red-100 text-red-700', icon: AlertCircle },
};

export const PreviewPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const [previews, setPreviews] = useState<PreviewInstance[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [selectedPreview, setSelectedPreview] = useState<PreviewInstance | null>(null);
  const [logs, setLogs] = useState('');
  const [isLoadingLogs, setIsLoadingLogs] = useState(false);

  useEffect(() => {
    if (projectId) {
      fetchPreviews();
    }
  }, [projectId]);

  // Polling pour mettre à jour le statut
  useEffect(() => {
    const interval = setInterval(() => {
      if (previews.some(p => p.status === 'building')) {
        fetchPreviews();
      }
    }, 5000);
    
    return () => clearInterval(interval);
  }, [previews, projectId]);

  const fetchPreviews = async () => {
    try {
      const response = await fetch(`/api/projects/${projectId}/previews`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
      });
      if (response.ok) {
        setPreviews(await response.json());
      }
    } catch (error) {
      toast.error('Erreur lors du chargement des préviews');
    } finally {
      setIsLoading(false);
    }
  };

  const createPreview = async () => {
    setIsCreating(true);
    try {
      // Utiliser le chemin du workspace par défaut
      const workspacePath = `/workspace/project-${projectId}`;
      
      const response = await fetch(`/api/projects/${projectId}/previews`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({ workspace_path: workspacePath })
      });

      if (response.ok) {
        toast.success('Preview en cours de création...');
        fetchPreviews();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Erreur lors de la création');
      }
    } catch (error) {
      toast.error('Erreur lors de la création du preview');
    } finally {
      setIsCreating(false);
    }
  };

  const stopPreview = async (previewId: string) => {
    if (!confirm('Voulez-vous arrêter ce preview ?')) return;

    try {
      const response = await fetch(`/api/projects/${projectId}/previews/${previewId}/stop`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
      });

      if (response.ok) {
        toast.success('Preview arrêté');
        fetchPreviews();
      } else {
        toast.error('Erreur lors de l\'arrêt');
      }
    } catch (error) {
      toast.error('Erreur lors de l\'arrêt');
    }
  };

  const loadLogs = async (preview: PreviewInstance) => {
    setSelectedPreview(preview);
    setIsLoadingLogs(true);
    
    try {
      const response = await fetch(`/api/projects/${projectId}/previews/${preview.id}/logs`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setLogs(data.logs || 'Aucun log disponible');
      }
    } catch (error) {
      setLogs('Erreur lors du chargement des logs');
    } finally {
      setIsLoadingLogs(false);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('fr-FR');
  };

  const getTimeRemaining = (expiresAt: string) => {
    const now = new Date();
    const expires = new Date(expiresAt);
    const diff = expires.getTime() - now.getTime();
    
    if (diff <= 0) return 'Expiré';
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    return `${hours}h ${minutes}m restantes`;
  };

  const activePreviews = previews.filter(p => p.status === 'running' || p.status === 'building');
  const canCreateNew = activePreviews.length < 3;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link to={`/projects/${projectId}`} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                <ArrowLeft className="w-5 h-5 text-gray-600" />
              </Link>
              <div>
                <h1 className="text-lg font-semibold text-gray-900">Déploiement Preview</h1>
                <p className="text-sm text-gray-500">
                  {activePreviews.length}/3 instances actives
                </p>
              </div>
            </div>
            
            <Button 
              onClick={createPreview} 
              isLoading={isCreating}
              disabled={!canCreateNew}
            >
              <Rocket className="w-4 h-4 mr-2" />
              Nouveau Preview
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {previews.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
            <Rocket className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Aucun preview</h2>
            <p className="text-gray-500 mb-6">
              Créez un environnement de prévisualisation pour tester votre application
            </p>
            <Button onClick={createPreview} disabled={!canCreateNew}>
              <Rocket className="w-4 h-4 mr-2" />
              Créer un Preview
            </Button>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Previews Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {previews.map((preview) => {
                const status = statusConfig[preview.status as keyof typeof statusConfig] || statusConfig.error;
                const StatusIcon = status.icon;
                const isActive = preview.status === 'running';
                
                return (
                  <div 
                    key={preview.id}
                    className={`bg-white rounded-xl shadow-sm border-2 overflow-hidden ${
                      selectedPreview?.id === preview.id ? 'border-primary-500' : 'border-gray-200'
                    }`}
                  >
                    <div className="p-4">
                      <div className="flex items-center justify-between mb-3">
                        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${status.color}`}>
                          <StatusIcon className={`w-3 h-3 ${preview.status === 'building' ? 'animate-spin' : ''}`} />
                          {status.label}
                        </span>
                        <button
                          onClick={() => loadLogs(preview)}
                          className="p-1 hover:bg-gray-100 rounded"
                        >
                          <Terminal className="w-4 h-4 text-gray-400" />
                        </button>
                      </div>
                      
                      <div className="space-y-2">
                        <p className="text-sm text-gray-500">
                          <Clock className="w-3 h-3 inline mr-1" />
                          Expire: {getTimeRemaining(preview.expires_at)}
                        </p>
                        <p className="text-sm text-gray-500">
                          Port: {preview.port}
                        </p>
                        <p className="text-xs text-gray-400">
                          Créé: {formatDate(preview.created_at)}
                        </p>
                      </div>
                    </div>
                    
                    <div className="px-4 py-3 bg-gray-50 border-t border-gray-100 flex gap-2">
                      {isActive && preview.url && (
                        <a href={preview.url} target="_blank" rel="noopener noreferrer" className="flex-1">
                          <Button variant="primary" size="sm" className="w-full">
                            <ExternalLink className="w-4 h-4 mr-1" />
                            Ouvrir
                          </Button>
                        </a>
                      )}
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => stopPreview(preview.id)}
                        disabled={preview.status !== 'running'}
                      >
                        <Square className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Logs Panel */}
            {selectedPreview && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="p-4 border-b border-gray-200 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Terminal className="w-5 h-5 text-gray-500" />
                    <h3 className="font-semibold text-gray-900">Logs - {selectedPreview.id}</h3>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => loadLogs(selectedPreview)}
                    >
                      <RefreshCw className="w-4 h-4" />
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => setSelectedPreview(null)}
                    >
                      Fermer
                    </Button>
                  </div>
                </div>
                <div className="p-4 bg-gray-900 rounded-b-xl">
                  {isLoadingLogs ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                    </div>
                  ) : (
                    <pre className="text-sm text-gray-300 font-mono overflow-x-auto max-h-96">
                      {logs || 'Aucun log disponible'}
                    </pre>
                  )}
                </div>
              </div>
            )}

            {/* Info Card */}
            <div className="bg-blue-50 rounded-xl p-4 border border-blue-200">
              <h4 className="font-medium text-blue-900 mb-2">💡 Comment ça marche</h4>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• Les préviews sont des containers Docker éphémères</li>
                <li>• Ils expirent automatiquement après 2 heures</li>
                <li>• Maximum 3 préviews actifs simultanément</li>
                <li>• Le code généré par OpenHands est automatiquement déployé</li>
              </ul>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default PreviewPage;