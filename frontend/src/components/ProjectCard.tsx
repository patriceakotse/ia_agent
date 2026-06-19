import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Folder, Clock, FileText, Play, MoreVertical,
  CheckCircle, AlertCircle, Loader2, XCircle
} from 'lucide-react';
import type { Project } from '../types';
import { Button } from './ui/Button';

interface ProjectCardProps {
  project: Project;
  onDelete?: (id: number) => void;
}

const statusConfig = {
  draft: { label: 'Brouillon', color: 'bg-gray-100 text-gray-700', icon: FileText },
  analyzing: { label: 'Analyse IA', color: 'bg-blue-100 text-blue-700', icon: Loader2 },
  validating: { label: 'Validation', color: 'bg-yellow-100 text-yellow-700', icon: Clock },
  in_progress: { label: 'En cours', color: 'bg-purple-100 text-purple-700', icon: Play },
  completed: { label: 'Terminé', color: 'bg-green-100 text-green-700', icon: CheckCircle },
  error: { label: 'Erreur', color: 'bg-red-100 text-red-700', icon: AlertCircle },
};

export const ProjectCard: React.FC<ProjectCardProps> = ({ project, onDelete }) => {
  const [showMenu, setShowMenu] = React.useState(false);
  const status = statusConfig[project.status] || statusConfig.draft;
  const StatusIcon = status.icon;

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
      <div className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary-50 rounded-lg">
              <Folder className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 line-clamp-1">{project.name}</h3>
              {project.client && (
                <p className="text-sm text-gray-500">{project.client}</p>
              )}
            </div>
          </div>
          
          <div className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="p-1 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <MoreVertical className="w-5 h-5 text-gray-400" />
            </button>
            
            {showMenu && (
              <div className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10">
                <Link
                  to={`/projects/${project.id}`}
                  className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  Voir les détails
                </Link>
                {project.status === 'in_progress' && (
                  <a
                    href={`/session/${project.id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block px-4 py-2 text-sm text-primary-600 hover:bg-gray-50"
                  >
                    Ouvrir dans OpenHands
                  </a>
                )}
                {onDelete && (
                  <button
                    onClick={() => {
                      onDelete(project.id);
                      setShowMenu(false);
                    }}
                    className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                  >
                    Supprimer
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
        
        {project.description && (
          <p className="text-sm text-gray-600 mb-4 line-clamp-2">{project.description}</p>
        )}
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${status.color}`}>
              <StatusIcon className={`w-3 h-3 ${project.status === 'analyzing' ? 'animate-spin' : ''}`} />
              {status.label}
            </span>
            
            <span className="text-xs text-gray-500 flex items-center gap-1">
              <FileText className="w-3 h-3" />
              {project.documents_count} doc{project.documents_count !== 1 ? 's' : ''}
            </span>
          </div>
          
          <span className="text-xs text-gray-400">
            {formatDate(project.updated_at || project.created_at)}
          </span>
        </div>
      </div>
      
      <div className="px-5 py-3 bg-gray-50 border-t border-gray-100">
        <Link to={`/projects/${project.id}`}>
          <Button variant="secondary" size="sm" className="w-full">
            {project.status === 'draft' ? 'Commencer' : 
             project.status === 'in_progress' ? 'Reprendre' : 
             'Voir'}
          </Button>
        </Link>
      </div>
    </div>
  );
};