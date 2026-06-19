import React, { useState, useEffect } from 'react';
import { 
  Settings, Key, Globe, Bot, Save, RotateCcw,
  Eye, EyeOff, CheckCircle, XCircle, Loader2,
  ChevronDown, ChevronRight, Shield, Zap
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import toast from 'react-hot-toast';

interface APIKeys {
  openai_configured: boolean;
  anthropic_configured: boolean;
  xai_configured: boolean;
  openai_key_preview: string;
  anthropic_key_preview: string;
  xai_key_preview: string;
}

interface OpenHandsSettings {
  url: string;
  api_key_configured: boolean;
  api_key_preview: string;
}

interface GeneralSettings {
  app_name: string;
  debug: boolean;
  version: string;
}

interface SettingsOverview {
  api_keys: APIKeys;
  openhands: OpenHandsSettings;
  general: GeneralSettings;
  env_file_exists: boolean;
}

export const AdminSettingsPage: React.FC = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    api_keys: true,
    openhands: false,
    general: false,
  });

  // API Keys state
  const [openaiKey, setOpenaiKey] = useState('');
  const [anthropicKey, setAnthropicKey] = useState('');
  const [xaiKey, setXaiKey] = useState('');
  const [showOpenAI, setShowOpenAI] = useState(false);
  const [showAnthropic, setShowAnthropic] = useState(false);
  const [showXAI, setShowXAI] = useState(false);

  // OpenHands state
  const [openhandsUrl, setOpenhandsUrl] = useState('');
  const [openhandsKey, setOpenhandsKey] = useState('');
  const [showOpenHandsKey, setShowOpenHandsKey] = useState(false);

  // General state
  const [appName, setAppName] = useState('');
  const [debugMode, setDebugMode] = useState(false);
  const [version, setVersion] = useState('');

  // Test results
  const [testResults, setTestResults] = useState<Record<string, { success: boolean; error?: string }>>({});

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await fetch('/api/admin/settings/overview', {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
      });
      
      if (response.ok) {
        const data: SettingsOverview = await response.json();
        
        // Update state
        setOpenhandsUrl(data.openhands.url);
        setAppName(data.general.app_name);
        setDebugMode(data.general.debug);
        setVersion(data.general.version);
        
        // Set previews (not actual keys)
        setTestResults({
          openai: { success: data.api_keys.openai_configured },
          anthropic: { success: data.api_keys.anthropic_configured },
          xai: { success: data.api_keys.xai_configured },
        });
      }
    } catch (error) {
      toast.error('Erreur lors du chargement des paramètres');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const saveAPIKeys = async () => {
    setIsSaving(true);
    try {
      const response = await fetch('/api/admin/settings/api-keys', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          openai_api_key: openaiKey || undefined,
          anthropic_api_key: anthropicKey || undefined,
          xai_api_key: xaiKey || undefined,
        })
      });

      if (response.ok) {
        toast.success('Clés API enregistrées');
        setOpenaiKey('');
        setAnthropicKey('');
        setXaiKey('');
        fetchSettings();
      } else {
        toast.error('Erreur lors de l\'enregistrement');
      }
    } catch (error) {
      toast.error('Erreur lors de l\'enregistrement');
    } finally {
      setIsSaving(false);
    }
  };

  const saveOpenHands = async () => {
    setIsSaving(true);
    try {
      const response = await fetch('/api/admin/settings/openhands', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          url: openhandsUrl,
          api_key: openhandsKey || undefined,
        })
      });

      if (response.ok) {
        toast.success('Paramètres OpenHands enregistrés');
        setOpenhandsKey('');
        fetchSettings();
      } else {
        toast.error('Erreur lors de l\'enregistrement');
      }
    } catch (error) {
      toast.error('Erreur lors de l\'enregistrement');
    } finally {
      setIsSaving(false);
    }
  };

  const saveGeneral = async () => {
    setIsSaving(true);
    try {
      const response = await fetch('/api/admin/settings/general', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          app_name: appName,
          debug: debugMode,
        })
      });

      if (response.ok) {
        toast.success('Paramètres généraux enregistrés');
        fetchSettings();
      } else {
        toast.error('Erreur lors de l\'enregistrement');
      }
    } catch (error) {
      toast.error('Erreur lors de l\'enregistrement');
    } finally {
      setIsSaving(false);
    }
  };

  const testAPIKey = async (provider: string) => {
    setIsTesting(provider);
    try {
      const response = await fetch(`/api/admin/settings/api-keys/test?provider=${provider}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
      });
      
      const data = await response.json();
      setTestResults(prev => ({
        ...prev,
        [provider]: { success: data.success, error: data.error }
      }));
      
      if (data.success) {
        toast.success(`✓ ${provider} fonctionne !`);
      } else {
        toast.error(`✗ ${provider}: ${data.error}`);
      }
    } catch (error) {
      toast.error('Erreur lors du test');
    } finally {
      setIsTesting(null);
    }
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
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary-100 rounded-lg">
                <Settings className="w-5 h-5 text-primary-600" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-gray-900">Paramètres Admin</h1>
                <p className="text-sm text-gray-500">Configurer l'application</p>
              </div>
            </div>
            <div className="text-sm text-gray-500">
              Version {version}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-4">
        
        {/* API Keys Section */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <button
            onClick={() => toggleSection('api_keys')}
            className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Key className="w-5 h-5 text-green-600" />
              </div>
              <div className="text-left">
                <h2 className="font-semibold text-gray-900">Clés API</h2>
                <p className="text-sm text-gray-500">Configurer les providers LLM</p>
              </div>
            </div>
            {expandedSections.api_keys ? (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronRight className="w-5 h-5 text-gray-400" />
            )}
          </button>

          {expandedSections.api_keys && (
            <div className="p-4 border-t border-gray-200 space-y-6">
              {/* Status Cards */}
              <div className="grid grid-cols-3 gap-4">
                <StatusCard
                  name="OpenAI"
                  icon={<Zap className="w-5 h-5" />}
                  color="green"
                  configured={testResults.openai?.success}
                  preview={testResults.openai?.success ? 'Configuré' : 'Non configuré'}
                />
                <StatusCard
                  name="Anthropic"
                  icon={<Bot className="w-5 h-5" />}
                  color="purple"
                  configured={testResults.anthropic?.success}
                  preview={testResults.anthropic?.success ? 'Configuré' : 'Non configuré'}
                />
                <StatusCard
                  name="xAI (Grok)"
                  icon={<Zap className="w-5 h-5" />}
                  color="orange"
                  configured={testResults.xai?.success}
                  preview={testResults.xai?.success ? 'Configuré' : 'Non configuré'}
                />
              </div>

              {/* OpenAI */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">OpenAI API Key</label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <input
                      type={showOpenAI ? 'text' : 'password'}
                      value={openaiKey}
                      onChange={(e) => setOpenaiKey(e.target.value)}
                      placeholder="sk-..."
                      className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                    <button
                      type="button"
                      onClick={() => setShowOpenAI(!showOpenAI)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600"
                    >
                      {showOpenAI ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => testAPIKey('openai')}
                    disabled={isTesting === 'openai'}
                  >
                    {isTesting === 'openai' ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Tester'}
                  </Button>
                </div>
              </div>

              {/* Anthropic */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">Anthropic API Key</label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <input
                      type={showAnthropic ? 'text' : 'password'}
                      value={anthropicKey}
                      onChange={(e) => setAnthropicKey(e.target.value)}
                      placeholder="sk-ant-..."
                      className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                    <button
                      type="button"
                      onClick={() => setShowAnthropic(!showAnthropic)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600"
                    >
                      {showAnthropic ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => testAPIKey('anthropic')}
                    disabled={isTesting === 'anthropic'}
                  >
                    {isTesting === 'anthropic' ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Tester'}
                  </Button>
                </div>
              </div>

              {/* xAI */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">xAI API Key</label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <input
                      type={showXAI ? 'text' : 'password'}
                      value={xaiKey}
                      onChange={(e) => setXaiKey(e.target.value)}
                      placeholder="xai-..."
                      className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                    <button
                      type="button"
                      onClick={() => setShowXAI(!showXAI)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600"
                    >
                      {showXAI ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => testAPIKey('xai')}
                    disabled={isTesting === 'xai'}
                  >
                    {isTesting === 'xai' ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Tester'}
                  </Button>
                </div>
              </div>

              <Button onClick={saveAPIKeys} isLoading={isSaving} className="w-full">
                <Save className="w-4 h-4 mr-2" />
                Sauvegarder les clés API
              </Button>
            </div>
          )}
        </div>

        {/* OpenHands Section */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <button
            onClick={() => toggleSection('openhands')}
            className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Bot className="w-5 h-5 text-purple-600" />
              </div>
              <div className="text-left">
                <h2 className="font-semibold text-gray-900">OpenHands</h2>
                <p className="text-sm text-gray-500">Configuration du serveur</p>
              </div>
            </div>
            {expandedSections.openhands ? (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronRight className="w-5 h-5 text-gray-400" />
            )}
          </button>

          {expandedSections.openhands && (
            <div className="p-4 border-t border-gray-200 space-y-4">
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">URL du serveur</label>
                <input
                  type="text"
                  value={openhandsUrl}
                  onChange={(e) => setOpenhandsUrl(e.target.value)}
                  placeholder="http://localhost:3000"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">API Key</label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <input
                      type={showOpenHandsKey ? 'text' : 'password'}
                      value={openhandsKey}
                      onChange={(e) => setOpenhandsKey(e.target.value)}
                      placeholder="Laisser vide pour garder l'actuelle"
                      className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                    <button
                      type="button"
                      onClick={() => setShowOpenHandsKey(!showOpenHandsKey)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600"
                    >
                      {showOpenHandsKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              </div>

              <Button onClick={saveOpenHands} isLoading={isSaving} className="w-full">
                <Save className="w-4 h-4 mr-2" />
                Sauvegarder OpenHands
              </Button>
            </div>
          )}
        </div>

        {/* General Section */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <button
            onClick={() => toggleSection('general')}
            className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Settings className="w-5 h-5 text-blue-600" />
              </div>
              <div className="text-left">
                <h2 className="font-semibold text-gray-900">Paramètres généraux</h2>
                <p className="text-sm text-gray-500">Configuration de l'application</p>
              </div>
            </div>
            {expandedSections.general ? (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronRight className="w-5 h-5 text-gray-400" />
            )}
          </button>

          {expandedSections.general && (
            <div className="p-4 border-t border-gray-200 space-y-4">
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">Nom de l'application</label>
                <input
                  type="text"
                  value={appName}
                  onChange={(e) => setAppName(e.target.value)}
                  placeholder="Agent Orchestrator"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">Mode Debug</p>
                  <p className="text-sm text-gray-500">Afficher les logs détaillés</p>
                </div>
                <button
                  onClick={() => setDebugMode(!debugMode)}
                  className={`relative w-12 h-6 rounded-full transition-colors ${
                    debugMode ? 'bg-primary-600' : 'bg-gray-300'
                  }`}
                >
                  <span
                    className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                      debugMode ? 'left-7' : 'left-1'
                    }`}
                  />
                </button>
              </div>

              <Button onClick={saveGeneral} isLoading={isSaving} className="w-full">
                <Save className="w-4 h-4 mr-2" />
                Sauvegarder les paramètres
              </Button>
            </div>
          )}
        </div>

        {/* Info Card */}
        <div className="bg-blue-50 rounded-xl p-4 border border-blue-200">
          <h4 className="font-medium text-blue-900 mb-2">💡 Note</h4>
          <p className="text-sm text-blue-700">
            Les modifications des clés API nécessitent un redémarrage de l'application pour prendre effet.
            Les paramètres sont sauvegardés dans le fichier <code className="bg-blue-100 px-1 rounded">.env</code>.
          </p>
        </div>
      </main>
    </div>
  );
};

// Status Card Component
const StatusCard: React.FC<{
  name: string;
  icon: React.ReactNode;
  color: 'green' | 'purple' | 'orange';
  configured: boolean;
  preview: string;
}> = ({ name, icon, color, configured, preview }) => {
  const colors = {
    green: 'bg-green-50 border-green-200 text-green-800',
    purple: 'bg-purple-50 border-purple-200 text-purple-800',
    orange: 'bg-orange-50 border-orange-200 text-orange-800',
  };

  return (
    <div className={`p-3 rounded-lg border ${colors[color]}`}>
      <div className="flex items-center gap-2 mb-1">
        {icon}
        <span className="font-medium text-sm">{name}</span>
      </div>
      <div className="flex items-center gap-1 text-xs">
        {configured ? (
          <CheckCircle className="w-3 h-3 text-green-600" />
        ) : (
          <XCircle className="w-3 h-3 text-red-500" />
        )}
        <span>{preview}</span>
      </div>
    </div>
  );
};

export default AdminSettingsPage;
