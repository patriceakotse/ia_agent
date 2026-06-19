import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, Search, Filter, Settings } from 'lucide-react';
import { projectsApi } from '../services/api';
import { useAuthStore } from '../store/authStore';
import { ProjectCard } from '../components/ProjectCard';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import toast from 'react-hot-toast';
import type { Project, ProjectStatus } from '../types';

export const DashboardPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<ProjectStatus | ''>('');
  const [showNewProjectModal, setShowNewProjectModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectClient, setNewProjectClient] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const fetchProjects = async () => {
    try {
      const response = await projectsApi.list({
        search: search || undefined,
        status: statusFilter || undefined,
      });
      setProjects(response.data);
    } catch (error) {
      toast.error('Erreur lors du chargement des projets');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [search, statusFilter]);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) {
      toast.error('Le nom du projet est requis');
      return;
    }
    
    setIsCreating(true);
    try {
      const response = await projectsApi.create({
        name: newProjectName,
        client: newProjectClient || undefined,
      });
      toast.success('Projet créé avec succès');
      setShowNewProjectModal(false);
      setNewProjectName('');
      setNewProjectClient('');
      navigate(`/projects/${response.data.id}`);
    } catch (error) {
      toast.error('Erreur lors de la création du projet');
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteProject = async (id: number) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce projet ?')) return;
    
    try {
      await projectsApi.delete(id);
      toast.success('Projet supprimé');
      fetchProjects();
    } catch {
      toast.error('Erreur lors de la suppression');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-xl font-bold text-gray-900">Agent Orchestrator</h1>
            
            <div className="flex items-center gap-4">
              <Link
                to="/admin/settings"
                className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <Settings className="w-4 h-4" />
                Paramètres
              </Link>
              <span className="text-sm text-gray-600">
                {user?.full_name || user?.username}
              </span>
              <button
                onClick={logout}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Déconnexion
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Toolbar */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Mes Projets</h2>
            <p className="text-gray-600 mt-1">
              {projects.length} projet{projects.length !== 1 ? 's' : ''}
            </p>
          </div>
          
          <Button onClick={() => setShowNewProjectModal(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Nouveau Projet
          </Button>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Rechercher un projet..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as ProjectStatus | '')}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">Tous les statuts</option>
            <option value="draft">Brouillon</option>
            <option value="analyzing">Analyse IA</option>
            <option value="validating">Validation</option>
            <option value="in_progress">En cours</option>
            <option value="completed">Terminé</option>
          </select>
        </div>

        {/* Projects Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-xl border border-gray-200 p-5 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-1/2 mb-4" />
                <div className="h-3 bg-gray-200 rounded w-3/4 mb-2" />
                <div className="h-3 bg-gray-200 rounded w-1/4" />
              </div>
            ))}
          </div>
        ) : projects.length === 0 ? (
          <div className="text-center py-16">
            <div className="text-6xl mb-4">📋</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Aucun projet</h3>
            <p className="text-gray-600 mb-6">
              {search || statusFilter
                ? 'Aucun projet ne correspond à vos critères'
                : 'Commencez par créer votre premier projet'}
            </p>
            {!search && !statusFilter && (
              <Button onClick={() => setShowNewProjectModal(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Créer un projet
              </Button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onDelete={handleDeleteProject}
              />
            ))}
          </div>
        )}
      </main>

      {/* New Project Modal */}
      {showNewProjectModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Nouveau Projet</h3>
            
            <form onSubmit={handleCreateProject} className="space-y-4">
              <Input
                label="Nom du projet *"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                placeholder="Mon Application Web"
                required
              />
              
              <Input
                label="Client"
                value={newProjectClient}
                onChange={(e) => setNewProjectClient(e.target.value)}
                placeholder="Entreprise ABC"
              />
              
              <div className="flex gap-3 pt-4">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => setShowNewProjectModal(false)}
                  className="flex-1"
                >
                  Annuler
                </Button>
                <Button type="submit" isLoading={isCreating} className="flex-1">
                  Créer
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};