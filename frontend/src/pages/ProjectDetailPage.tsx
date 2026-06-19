import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, Play, CheckCircle, FileText, Loader2, 
  Send, ExternalLink, AlertCircle, Clock, Bot,
  GitBranch, Settings, Users, AlertTriangle, Rocket, RefreshCw
} from 'lucide-react';
import { projectsApi, documentsApi, sessionsApi } from '../services/api';
import { Button } from '../components/ui/Button';
import { Textarea } from '../components/ui/Input';
import { MonacoEditor } from '../components/MonacoEditor';
import { DocumentHistory } from '../components/DocumentHistory';
import toast from 'react-hot-toast';
import type { ProjectDetail, Document, Session, Log, DocumentType } from '../types';

const documentTabs: { type: DocumentType; label: string; icon: React.ElementType }[] = [
  { type: 'readme', label: 'README', icon: FileText },
  { type: 'specs', label: 'Spécifications', icon: FileText },
  { type: 'tasks', label: 'User Stories', icon: FileText },
  { type: 'db_schema', label: 'MCD', icon: FileText },
  { type: 'workflow', label: 'Workflow', icon: FileText },
  { type: 'marketing', label: 'Marketing', icon: FileText },
];

const statusSteps = [
  { key: 'draft', label: 'Brouillon' },
  { key: 'analyzing', label: 'Analyse IA' },
  { key: 'validating', label: 'Validation' },
  { key: 'in_progress', label: 'Développement' },
  { key: 'completed', label: 'Terminé' },
];

export const ProjectDetailPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<DocumentType>('readme');
  const [meetingNotes, setMeetingNotes] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isLaunching, setIsLaunching] = useState(false);
  const [editingContent, setEditingContent] = useState('');
  const [originalContent, setOriginalContent] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [isSendingFeedback, setIsSendingFeedback] = useState(false);
  const [logs, setLogs] = useState<Log[]>([]);
  const [activeSession, setActiveSession] = useState<Session | null>(null);
  
  // Nouvelles fonctionnalités
  const [selectedModel, setSelectedModel] = useState<string>('gpt-4');
  const [alerts, setAlerts] = useState<any[]>([]);
  const [showGitPanel, setShowGitPanel] = useState(false);
  const [showSettingsPanel, setShowSettingsPanel] = useState(false);
  const [showHistoryPanel, setShowHistoryPanel] = useState(false);
  const [documentVersions, setDocumentVersions] = useState<any[]>([]);
  const [isRestoring, setIsRestoring] = useState(false);

  const fetchProject = useCallback(async () => {
    if (!projectId) return;
    try {
      const response = await projectsApi.get(parseInt(projectId));
      setProject(response.data);
      if (response.data.meeting_notes) {
        setMeetingNotes(response.data.meeting_notes);
      }
      // Trouver la session active
      const runningSession = response.data.sessions.find(s => s.status === 'running');
      setActiveSession(runningSession || null);
    } catch (error) {
      toast.error('Erreur lors du chargement du projet');
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchProject();
  }, [fetchProject]);

  // Polling pour les logs si une session est active
  useEffect(() => {
    if (!activeSession) return;

    const pollLogs = async () => {
      try {
        const response = await sessionsApi.getLogs(parseInt(projectId!), activeSession.id);
        setLogs(response.data.slice(-50)); // Garder les 50 derniers logs
      } catch (error) {
        console.error('Erreur polling logs');
      }
    };

    pollLogs();
    const interval = setInterval(pollLogs, 3000);
    return () => clearInterval(interval);
  }, [activeSession, projectId]);

  // Mettre à jour le contenu en édition quand on change d'onglet
  useEffect(() => {
    if (project?.documents) {
      const doc = project.documents.find(d => d.doc_type === activeTab);
      if (doc) {
        setEditingContent(doc.content || '');
        setOriginalContent(doc.content || '');
        // Charger l'historique des versions
        fetchDocumentVersions(doc.doc_type);
      }
    }
  }, [activeTab, project]);

  // Fonction pour charger l'historique des versions
  const fetchDocumentVersions = async (docType: string) => {
    if (!projectId) return;
    try {
      const response = await fetch(`/api/projects/${projectId}/documents/${docType}/versions`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
      });
      if (response.ok) {
        const versions = await response.json();
        setDocumentVersions(versions);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des versions:', error);
    }
  };

  // Fonction pour restaurer une version
  const handleRestoreVersion = async (version: any) => {
    if (!projectId) return;
    setIsRestoring(true);
    try {
      const response = await fetch(`/api/projects/${projectId}/documents/${activeTab}/restore/${version.version}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
      });
      if (response.ok) {
        toast.success(`Version ${version.version} restaurée`);
        await fetchProject();
        fetchDocumentVersions(activeTab);
      } else {
        toast.error('Erreur lors de la restauration');
      }
    } catch (error) {
      toast.error('Erreur lors de la restauration');
    } finally {
      setIsRestoring(false);
    }
  };

  // Fonction pour analyser les logs et détecter les alertes
  const analyzeLogsForAlerts = (newLogs: Log[]) => {
    const newAlerts: any[] = [];
    
    newLogs.forEach(log => {
      // Détecter les boucles d'erreurs
      if (log.message.includes('Retrying') || log.message.includes('Same error')) {
        newAlerts.push({
          type: 'loop',
          severity: 'warning',
          message: 'Comportement en boucle détecté',
          timestamp: log.timestamp
        });
      }
      
      // Détecter les erreurs de compilation
      if (log.level === 'ERROR' && (
        log.message.includes('SyntaxError') || 
        log.message.includes('TypeError') ||
        log.message.includes('ImportError')
      )) {
        newAlerts.push({
          type: 'compilation_error',
          severity: 'error',
          message: log.message.substring(0, 100),
          timestamp: log.timestamp
        });
      }
    });
    
    setAlerts(prev => [...prev, ...newAlerts].slice(-10)); // Garder les 10 dernières alertes
  };

  const handleAnalyze = async () => {
    if (!projectId || !meetingNotes.trim()) {
      toast.error('Veuillez entrer le compte-rendu de réunion');
      return;
    }

    setIsAnalyzing(true);
    try {
      const response = await projectsApi.analyze(parseInt(projectId), meetingNotes);
      toast.success('Documents générés avec succès !');
      await fetchProject();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors de l\'analyse');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleValidate = async () => {
    if (!projectId) return;
    
    setIsSaving(true);
    try {
      await documentsApi.update(parseInt(projectId), activeTab, { is_validated: true });
      toast.success('Document validé');
      await fetchProject();
    } catch (error) {
      toast.error('Erreur lors de la validation');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveContent = async () => {
    if (!projectId) return;
    
    setIsSaving(true);
    try {
      await documentsApi.update(parseInt(projectId), activeTab, { content: editingContent });
      toast.success('Document sauvegardé');
      await fetchProject();
    } catch (error) {
      toast.error('Erreur lors de la sauvegarde');
    } finally {
      setIsSaving(false);
    }
  };

  const handleLaunchOpenHands = async () => {
    if (!projectId) return;
    
    const validatedDocs = project?.documents.filter(d => d.is_validated);
    if (!validatedDocs || validatedDocs.length === 0) {
      toast.error('Validez au moins un document avant de lancer');
      return;
    }

    setIsLaunching(true);
    try {
      const response = await projectsApi.launch(parseInt(projectId));
      toast.success('OpenHands lancé !');
      
      // Ouvrir le lien deep link
      window.open(response.data.deep_link, '_blank');
      
      await fetchProject();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors du lancement');
    } finally {
      setIsLaunching(false);
    }
  };

  const handleSendFeedback = async () => {
    if (!projectId || !activeSession || !feedback.trim()) return;
    
    setIsSendingFeedback(true);
    try {
      await sessionsApi.sendFeedback(parseInt(projectId), activeSession.id, feedback);
      toast.success('Feedback envoyé');
      setFeedback('');
    } catch (error) {
      toast.error('Erreur lors de l\'envoi du feedback');
    } finally {
      setIsSendingFeedback(false);
    }
  };

  const getCurrentStepIndex = () => {
    if (!project) return 0;
    const index = statusSteps.findIndex(s => s.key === project.status);
    return index >= 0 ? index : 0;
  };

  const getDocument = (type: DocumentType): Document | undefined => {
    return project?.documents.find(d => d.doc_type === type);
  };

  const hasValidatedDocuments = project?.documents.some(d => d.is_validated) || false;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900">Projet non trouvé</h2>
          <Link to="/" className="text-primary-600 hover:underline mt-4 block">
            Retour au dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link to="/" className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                <ArrowLeft className="w-5 h-5 text-gray-600" />
              </Link>
              <div>
                <h1 className="text-lg font-semibold text-gray-900">{project.name}</h1>
                {project.client && (
                  <p className="text-sm text-gray-500">{project.client}</p>
                )}
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              {project.status === 'in_progress' && activeSession && (
                <a
                  href={`/session/${activeSession.openhands_session_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Button variant="secondary" size="sm">
                    <ExternalLink className="w-4 h-4 mr-2" />
                    Ouvrir OpenHands
                  </Button>
                </a>
              )}
              
              {project.status === 'validating' && hasValidatedDocuments && (
                <Button 
                  onClick={handleLaunchOpenHands} 
                  isLoading={isLaunching}
                  disabled={isLaunching}
                >
                  <Bot className="w-4 h-4 mr-2" />
                  Lancer OpenHands
                </Button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Progress Steps */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            {statusSteps.map((step, index) => {
              const isActive = index === getCurrentStepIndex();
              const isCompleted = index < getCurrentStepIndex();
              const isError = project.status === 'error' && isActive;
              
              return (
                <React.Fragment key={step.key}>
                  <div className="flex items-center">
                    <div className={`
                      w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                      ${isCompleted ? 'bg-green-500 text-white' : ''}
                      ${isActive && !isError ? 'bg-primary-600 text-white' : ''}
                      ${isError ? 'bg-red-500 text-white' : ''}
                      ${!isActive && !isCompleted ? 'bg-gray-200 text-gray-500' : ''}
                    `}>
                      {isCompleted ? (
                        <CheckCircle className="w-5 h-5" />
                      ) : isActive && !isError ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        index + 1
                      )}
                    </div>
                    <span className={`ml-2 text-sm font-medium ${
                      isActive || isCompleted ? 'text-gray-900' : 'text-gray-500'
                    }`}>
                      {step.label}
                    </span>
                  </div>
                  {index < statusSteps.length - 1 && (
                    <div className={`flex-1 h-1 mx-4 rounded ${
                      isCompleted ? 'bg-green-500' : 'bg-gray-200'
                    }`} />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Meeting Notes */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sticky top-24">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Compte-rendu de réunion
              </h2>
              
              <Textarea
                value={meetingNotes}
                onChange={(e) => setMeetingNotes(e.target.value)}
                placeholder="Collez ici le compte-rendu de votre réunion avec le client..."
                className="min-h-[300px] mb-4"
              />
              
              <Button 
                onClick={handleAnalyze} 
                isLoading={isAnalyzing}
                disabled={isAnalyzing || !meetingNotes.trim()}
                className="w-full"
              >
                {isAnalyzing ? 'Analyse en cours...' : 'Analyser et Générer'}
              </Button>
            </div>
          </div>

          {/* Right Column - Documents & Monitoring */}
          <div className="lg:col-span-2 space-y-6">
            {/* Documents Tabs */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="border-b border-gray-200">
                <div className="flex overflow-x-auto">
                  {documentTabs.map((tab) => {
                    const doc = getDocument(tab.type);
                    const Icon = tab.icon;
                    
                    return (
                      <button
                        key={tab.type}
                        onClick={() => setActiveTab(tab.type)}
                        className={`
                          flex items-center gap-2 px-4 py-3 text-sm font-medium whitespace-nowrap
                          border-b-2 transition-colors
                          ${activeTab === tab.type
                            ? 'border-primary-600 text-primary-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700'}
                        `}
                      >
                        <Icon className="w-4 h-4" />
                        {tab.label}
                        {doc?.is_validated && (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
              
              <div className="p-6">
                {project.documents.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>Aucun document généré</p>
                    <p className="text-sm mt-1">
                      Lancez l'analyse pour générer les documents
                    </p>
                  </div>
                ) : (
                  <>
                    {/* Barre d'outils du document */}
                    <div className="mb-4 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => setShowHistoryPanel(!showHistoryPanel)}
                        >
                          <Clock className="w-4 h-4 mr-1" />
                          Historique
                        </Button>
                        {activeTab === 'db_schema' && (
                          <span className="text-xs text-gray-500">
                            💡 Les diagrammes Mermaid sont automatiquement rendus
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <Button 
                          variant="secondary" 
                          size="sm"
                          onClick={handleValidate}
                          isLoading={isSaving}
                          disabled={getDocument(activeTab)?.is_validated}
                        >
                          <CheckCircle className="w-4 h-4 mr-2" />
                          {getDocument(activeTab)?.is_validated ? 'Validé' : 'Valider'}
                        </Button>
                      </div>
                    </div>

                    {/* Panneau historique */}
                    {showHistoryPanel && documentVersions.length > 0 && (
                      <div className="mb-4">
                        <DocumentHistory
                          versions={documentVersions}
                          currentVersion={getDocument(activeTab)?.version || 1}
                          onRestore={handleRestoreVersion}
                          isRestoring={isRestoring}
                        />
                      </div>
                    )}
                    
                    {/* Éditeur Monaco avec prévisualisation */}
                    <MonacoEditor
                      content={editingContent}
                      onChange={setEditingContent}
                      onSave={handleSaveContent}
                      isSaving={isSaving}
                      originalContent={originalContent}
                    />
                  </>
                )}
              </div>
            </div>

            {/* Active Session Monitoring */}
            {activeSession && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="p-4 border-b border-gray-200 bg-purple-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-purple-100 rounded-lg">
                        <Bot className="w-5 h-5 text-purple-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">Session OpenHands Active</h3>
                        <p className="text-sm text-gray-600">
                          Progression: {activeSession.progress}%
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4">
                      {/* Sélection du modèle LLM */}
                      <div className="flex items-center gap-2">
                        <label className="text-sm text-gray-600">Modèle:</label>
                        <select
                          value={selectedModel}
                          onChange={(e) => setSelectedModel(e.target.value)}
                          className="px-2 py-1 border border-gray-300 rounded text-sm"
                        >
                          <option value="gpt-4">GPT-4</option>
                          <option value="gpt-4-turbo">GPT-4 Turbo</option>
                          <option value="gpt-3.5-turbo">GPT-3.5</option>
                          <option value="claude-3-opus">Claude 3 Opus</option>
                          <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                        </select>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-purple-600 transition-all"
                            style={{ width: `${activeSession.progress}%` }}
                          />
                        </div>
                        {activeSession.current_task && (
                          <span className="text-sm text-gray-600">
                            {activeSession.current_task}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="p-4">
                  {/* Alertes intelligentes */}
                  {alerts.length > 0 && (
                    <div className="mb-4 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <AlertTriangle className="w-4 h-4 text-yellow-600" />
                        <span className="font-medium text-yellow-800">Alertes détectées</span>
                      </div>
                      {alerts.slice(-3).map((alert, idx) => (
                        <div key={idx} className="text-sm text-yellow-700 mb-1">
                          • {alert.message}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Logs */}
                  <div className="bg-gray-900 rounded-lg p-4 h-[200px] overflow-y-auto font-mono text-sm">
                    {logs.length === 0 ? (
                      <p className="text-gray-500">En attente de logs...</p>
                    ) : (
                      logs.map((log) => (
                        <div key={log.id} className="text-gray-300 mb-1">
                          <span className="text-gray-500">
                            {new Date(log.timestamp).toLocaleTimeString()}
                          </span>
                          {' '}
                          <span className={`
                            ${log.level === 'ERROR' ? 'text-red-400' : ''}
                            ${log.level === 'WARNING' ? 'text-yellow-400' : ''}
                            ${log.level === 'INFO' ? 'text-green-400' : ''}
                          `}>
                            [{log.level}]
                          </span>
                          {' '}
                          <span className="text-gray-200">{log.message}</span>
                        </div>
                      ))
                    )}
                  </div>
                  
                  {/* Feedback Input */}
                  <div className="mt-4 flex gap-2">
                    <input
                      type="text"
                      value={feedback}
                      onChange={(e) => setFeedback(e.target.value)}
                      placeholder="Envoyer des instructions à OpenHands..."
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      onKeyPress={(e) => e.key === 'Enter' && handleSendFeedback()}
                    />
                    <Button 
                      onClick={handleSendFeedback}
                      isLoading={isSendingFeedback}
                      disabled={!feedback.trim()}
                    >
                      <Send className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};