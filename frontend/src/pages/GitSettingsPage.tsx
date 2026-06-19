import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, GitBranch, Plus, Trash2, ExternalLink,
  Github, Gitlab, RefreshCw, Check, X, GitPullRequest
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import toast from 'react-hot-toast';

interface GitConnection {
  id: number;
  provider: string;
  owner: string;
  repo: string;
  default_branch: string;
}

interface Branch {
  name: string;
}

interface PullRequest {
  number: number;
  title: string;
  state: string;
  url: string;
  branch: string;
}

export const GitSettingsPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const [connections, setConnections] = useState<GitConnection[]>([]);
  const [branches, setBranches] = useState<string[]>([]);
  const [pullRequests, setPullRequests] = useState<PullRequest[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedConnection, setSelectedConnection] = useState<GitConnection | null>(null);
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [showPRModal, setShowPRModal] = useState(false);
  
  // Form state
  const [provider, setProvider] = useState('github');
  const [owner, setOwner] = useState('');
  const [repo, setRepo] = useState('');
  const [accessToken, setAccessToken] = useState('');
  const [branch, setBranch] = useState('main');
  
  // PR form
  const [prTitle, setPrTitle] = useState('');
  const [prDescription, setPrDescription] = useState('');
  const [prSourceBranch, setPrSourceBranch] = useState('');
  const [isConnecting, setIsConnecting] = useState(false);
  const [isCreatingPR, setIsCreatingPR] = useState(false);

  useEffect(() => {
    if (projectId) {
      fetchConnections();
    }
  }, [projectId]);

  const fetchConnections = async () => {
    try {
      const response = await fetch(`/api/projects/${projectId}/git/repos`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
      });
      if (response.ok) {
        const data = await response.json();
        setConnections(data);
        if (data.length > 0 && !selectedConnection) {
          selectConnection(data[0]);
        }
      }
    } catch (error) {
      toast.error('Erreur lors du chargement des connexions');
    } finally {
      setIsLoading(false);
    }
  };

  const selectConnection = async (conn: GitConnection) => {
    setSelectedConnection(conn);
    await fetchBranches(conn.id);
    await fetchPullRequests(conn.id);
  };

  const fetchBranches = async (connectionId: number) => {
    try {
      const response = await fetch(`/api/projects/${projectId}/git/branches?connection_id=${connectionId}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
      });
      if (response.ok) {
        setBranches(await response.json());
      }
    } catch (error) {
      console.error('Erreur lors du chargement des branches');
    }
  };

  const fetchPullRequests = async (connectionId: number) => {
    try {
      const response = await fetch(`/api/projects/${projectId}/git/pull-requests?connection_id=${connectionId}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
      });
      if (response.ok) {
        setPullRequests(await response.json());
      }
    } catch (error) {
      console.error('Erreur lors du chargement des PRs');
    }
  };

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!owner.trim() || !repo.trim() || !accessToken.trim()) {
      toast.error('Veuillez remplir tous les champs');
      return;
    }

    setIsConnecting(true);
    try {
      const response = await fetch(`/api/projects/${projectId}/git/connect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          provider,
          owner,
          repo,
          access_token: accessToken,
          default_branch: branch
        })
      });

      if (response.ok) {
        toast.success('Repository connecté avec succès');
        setShowConnectModal(false);
        resetForm();
        fetchConnections();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Erreur lors de la connexion');
      }
    } catch (error) {
      toast.error('Erreur lors de la connexion');
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async (connectionId: number) => {
    if (!confirm('Voulez-vous déconnecter ce repository ?')) return;

    try {
      const response = await fetch(`/api/projects/${projectId}/git/disconnect/${connectionId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
      });

      if (response.ok) {
        toast.success('Repository déconnecté');
        if (selectedConnection?.id === connectionId) {
          setSelectedConnection(null);
        }
        fetchConnections();
      } else {
        toast.error('Erreur lors de la déconnexion');
      }
    } catch (error) {
      toast.error('Erreur lors de la déconnexion');
    }
  };

  const handleCreateBranch = async () => {
    if (!selectedConnection) return;
    
    const branchName = prompt('Nom de la nouvelle branche:');
    if (!branchName) return;

    try {
      const response = await fetch(`/api/projects/${projectId}/git/branches?connection_id=${selectedConnection.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          name: branchName,
          from_branch: selectedConnection.default_branch
        })
      });

      if (response.ok) {
        toast.success('Branche créée');
        fetchBranches(selectedConnection.id);
      } else {
        toast.error('Erreur lors de la création de la branche');
      }
    } catch (error) {
      toast.error('Erreur lors de la création de la branche');
    }
  };

  const handleCreatePR = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedConnection || !prTitle.trim() || !prSourceBranch.trim()) {
      toast.error('Veuillez remplir tous les champs');
      return;
    }

    setIsCreatingPR(true);
    try {
      const response = await fetch(`/api/projects/${projectId}/git/pull-requests?connection_id=${selectedConnection.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          title: prTitle,
          description: prDescription,
          source_branch: prSourceBranch,
          target_branch: selectedConnection.default_branch
        })
      });

      if (response.ok) {
        const pr = await response.json();
        toast.success('Pull Request créée');
        setShowPRModal(false);
        setPrTitle('');
        setPrDescription('');
        setPrSourceBranch('');
        fetchPullRequests(selectedConnection.id);
        window.open(pr.url, '_blank');
      } else {
        toast.error('Erreur lors de la création de la PR');
      }
    } catch (error) {
      toast.error('Erreur lors de la création de la PR');
    } finally {
      setIsCreatingPR(false);
    }
  };

  const resetForm = () => {
    setProvider('github');
    setOwner('');
    setRepo('');
    setAccessToken('');
    setBranch('main');
  };

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
                <h1 className="text-lg font-semibold text-gray-900">Intégration Git</h1>
                <p className="text-sm text-gray-500">Gérez vos repositories et Pull Requests</p>
              </div>
            </div>
            
            <Button onClick={() => setShowConnectModal(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Connecter un repo
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {connections.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
            <GitBranch className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Aucun repository connecté</h2>
            <p className="text-gray-500 mb-6">
              Connectez un repository GitHub ou GitLab pour gérer vos branches et Pull Requests
            </p>
            <Button onClick={() => setShowConnectModal(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Connecter un repository
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Sidebar - Repositories */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="p-4 border-b border-gray-200">
                  <h3 className="font-semibold text-gray-900">Repositories</h3>
                </div>
                <div className="divide-y divide-gray-100">
                  {connections.map((conn) => (
                    <button
                      key={conn.id}
                      onClick={() => selectConnection(conn)}
                      className={`w-full p-4 text-left hover:bg-gray-50 transition-colors ${
                        selectedConnection?.id === conn.id ? 'bg-primary-50' : ''
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        {conn.provider === 'github' ? (
                          <Github className="w-5 h-5" />
                        ) : (
                          <Gitlab className="w-5 h-5" />
                        )}
                        <span className="font-medium text-gray-900 truncate">
                          {conn.repo}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500 mt-1">
                        {conn.owner}/{conn.repo}
                      </p>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Main Content */}
            <div className="lg:col-span-3 space-y-6">
              {selectedConnection && (
                <>
                  {/* Branches */}
                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                    <div className="p-4 border-b border-gray-200 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <GitBranch className="w-5 h-5 text-gray-500" />
                        <h3 className="font-semibold text-gray-900">Branches</h3>
                      </div>
                      <Button variant="ghost" size="sm" onClick={handleCreateBranch}>
                        <Plus className="w-4 h-4 mr-1" />
                        Nouvelle branche
                      </Button>
                    </div>
                    <div className="p-4 max-h-60 overflow-y-auto">
                      {branches.length === 0 ? (
                        <p className="text-gray-500 text-sm">Aucune branche trouvée</p>
                      ) : (
                        <div className="space-y-1">
                          {branches.map((b) => (
                            <div
                              key={b}
                              className={`px-3 py-2 rounded-lg text-sm ${
                                b === selectedConnection.default_branch
                                  ? 'bg-green-50 text-green-700 font-medium'
                                  : 'text-gray-700 hover:bg-gray-50'
                              }`}
                            >
                              <GitBranch className="w-4 h-4 inline mr-2" />
                              {b}
                              {b === selectedConnection.default_branch && (
                                <span className="ml-2 text-xs bg-green-100 px-2 py-0.5 rounded">
                                  default
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Pull Requests */}
                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                    <div className="p-4 border-b border-gray-200 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <GitPullRequest className="w-5 h-5 text-gray-500" />
                        <h3 className="font-semibold text-gray-900">Pull Requests</h3>
                      </div>
                      <Button variant="secondary" size="sm" onClick={() => setShowPRModal(true)}>
                        <Plus className="w-4 h-4 mr-1" />
                        Nouvelle PR
                      </Button>
                    </div>
                    <div className="divide-y divide-gray-100">
                      {pullRequests.length === 0 ? (
                        <div className="p-8 text-center text-gray-500">
                          <GitPullRequest className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                          <p>Aucune Pull Request</p>
                          <p className="text-sm mt-1">Créez une PR pour fusionner vos modifications</p>
                        </div>
                      ) : (
                        pullRequests.map((pr) => (
                          <a
                            key={pr.number}
                            href={pr.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                          >
                            <div className="flex items-center gap-3">
                              <div className={`p-1 rounded ${
                                pr.state === 'open' ? 'bg-green-100' : 'bg-purple-100'
                              }`}>
                                {pr.state === 'open' ? (
                                  <Plus className="w-4 h-4 text-green-600" />
                                ) : (
                                  <Check className="w-4 h-4 text-purple-600" />
                                )}
                              </div>
                              <div>
                                <p className="font-medium text-gray-900">{pr.title}</p>
                                <p className="text-sm text-gray-500">
                                  #{pr.number} • {pr.branch}
                                </p>
                              </div>
                            </div>
                            <ExternalLink className="w-4 h-4 text-gray-400" />
                          </a>
                        ))
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-900">
                          {selectedConnection.owner}/{selectedConnection.repo}
                        </p>
                        <p className="text-sm text-gray-500">
                          Branche par défaut: {selectedConnection.default_branch}
                        </p>
                      </div>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => handleDisconnect(selectedConnection.id)}
                      >
                        <Trash2 className="w-4 h-4 mr-1" />
                        Déconnecter
                      </Button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Connect Modal */}
      {showConnectModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-lg">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Connecter un Repository</h3>
            
            <form onSubmit={handleConnect} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setProvider('github')}
                    className={`flex-1 p-3 rounded-lg border-2 transition-colors ${
                      provider === 'github' ? 'border-primary-600 bg-primary-50' : 'border-gray-200'
                    }`}
                  >
                    <Github className="w-6 h-6 mx-auto mb-1" />
                    <span className="text-sm">GitHub</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setProvider('gitlab')}
                    className={`flex-1 p-3 rounded-lg border-2 transition-colors ${
                      provider === 'gitlab' ? 'border-primary-600 bg-primary-50' : 'border-gray-200'
                    }`}
                  >
                    <Gitlab className="w-6 h-6 mx-auto mb-1" />
                    <span className="text-sm">GitLab</span>
                  </button>
                </div>
              </div>
              
              <Input
                label="Owner / Organisation"
                value={owner}
                onChange={(e) => setOwner(e.target.value)}
                placeholder="mon-organisation"
                required
              />
              
              <Input
                label="Nom du repository"
                value={repo}
                onChange={(e) => setRepo(e.target.value)}
                placeholder="mon-projet"
                required
              />
              
              <Input
                label="Personal Access Token"
                type="password"
                value={accessToken}
                onChange={(e) => setAccessToken(e.target.value)}
                placeholder="ghp_xxxxxxxxxxxx"
                required
              />
              
              <Input
                label="Branche par défaut"
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
                placeholder="main"
              />
              
              <div className="flex gap-3 pt-4">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => { setShowConnectModal(false); resetForm(); }}
                  className="flex-1"
                >
                  Annuler
                </Button>
                <Button type="submit" isLoading={isConnecting} className="flex-1">
                  Connecter
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create PR Modal */}
      {showPRModal && selectedConnection && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-lg">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Créer une Pull Request</h3>
            
            <form onSubmit={handleCreatePR} className="space-y-4">
              <Input
                label="Titre"
                value={prTitle}
                onChange={(e) => setPrTitle(e.target.value)}
                placeholder="feat: Ajout de la fonctionnalité X"
                required
              />
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={prDescription}
                  onChange={(e) => setPrDescription(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg min-h-[100px]"
                  placeholder="Description des changements..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Branche source</label>
                <select
                  value={prSourceBranch}
                  onChange={(e) => setPrSourceBranch(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  required
                >
                  <option value="">Sélectionner une branche</option>
                  {branches.filter(b => b !== selectedConnection.default_branch).map((b) => (
                    <option key={b} value={b}>{b}</option>
                  ))}
                </select>
              </div>
              
              <p className="text-sm text-gray-500">
                Cible: {selectedConnection.default_branch}
              </p>
              
              <div className="flex gap-3 pt-4">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => setShowPRModal(false)}
                  className="flex-1"
                >
                  Annuler
                </Button>
                <Button type="submit" isLoading={isCreatingPR} className="flex-1">
                  Créer la PR
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default GitSettingsPage;