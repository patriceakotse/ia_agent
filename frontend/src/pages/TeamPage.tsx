import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, Users, Plus, Shield, Trash2, UserPlus,
  Crown, Wrench, Eye
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import toast from 'react-hot-toast';

interface TeamMember {
  id: number;
  user_id: number;
  username: string;
  email: string;
  full_name?: string;
  role: string;
  joined_at?: number;
}

interface Team {
  id: number;
  name: string;
  slug: string;
  plan: string;
  member_count: number;
}

const roleIcons: Record<string, React.ElementType> = {
  owner: Crown,
  admin: Wrench,
  editor: Wrench,
  viewer: Eye,
};

const roleColors: Record<string, string> = {
  owner: 'bg-yellow-100 text-yellow-700',
  admin: 'bg-purple-100 text-purple-700',
  editor: 'bg-blue-100 text-blue-700',
  viewer: 'bg-gray-100 text-gray-700',
};

export const TeamPage: React.FC = () => {
  const { teamId } = useParams<{ teamId: string }>();
  const [team, setTeam] = useState<Team | null>(null);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('viewer');
  const [isInviting, setIsInviting] = useState(false);

  useEffect(() => {
    if (teamId) {
      fetchTeam();
      fetchMembers();
    }
  }, [teamId]);

  const fetchTeam = async () => {
    try {
      const response = await fetch(`/api/teams/${teamId}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
      });
      if (response.ok) {
        setTeam(await response.json());
      }
    } catch (error) {
      toast.error('Erreur lors du chargement de l\'équipe');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchMembers = async () => {
    try {
      const response = await fetch(`/api/teams/${teamId}/members`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
      });
      if (response.ok) {
        setMembers(await response.json());
      }
    } catch (error) {
      toast.error('Erreur lors du chargement des membres');
    }
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail.trim()) return;

    setIsInviting(true);
    try {
      const response = await fetch(`/api/teams/${teamId}/members`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({ email: inviteEmail, role: inviteRole })
      });

      if (response.ok) {
        toast.success('Membre invité avec succès');
        setShowInviteModal(false);
        setInviteEmail('');
        fetchMembers();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Erreur lors de l\'invitation');
      }
    } catch (error) {
      toast.error('Erreur lors de l\'invitation');
    } finally {
      setIsInviting(false);
    }
  };

  const handleUpdateRole = async (userId: number, newRole: string) => {
    try {
      const response = await fetch(`/api/teams/${teamId}/members/${userId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({ role: newRole })
      });

      if (response.ok) {
        toast.success('Rôle mis à jour');
        fetchMembers();
      } else {
        toast.error('Erreur lors de la mise à jour du rôle');
      }
    } catch (error) {
      toast.error('Erreur lors de la mise à jour du rôle');
    }
  };

  const handleRemoveMember = async (userId: number) => {
    if (!confirm('Êtes-vous sûr de vouloir retirer ce membre ?')) return;

    try {
      const response = await fetch(`/api/teams/${teamId}/members/${userId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
      });

      if (response.ok) {
        toast.success('Membre retiré');
        fetchMembers();
      } else {
        toast.error('Erreur lors du retrait du membre');
      }
    } catch (error) {
      toast.error('Erreur lors du retrait du membre');
    }
  };

  const formatDate = (timestamp?: number) => {
    if (!timestamp) return '-';
    return new Date(timestamp * 1000).toLocaleDateString('fr-FR');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent" />
      </div>
    );
  }

  if (!team) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900">Équipe non trouvée</h2>
          <Link to="/dashboard" className="text-primary-600 hover:underline mt-4 block">
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
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link to="/dashboard" className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                <ArrowLeft className="w-5 h-5 text-gray-600" />
              </Link>
              <div>
                <h1 className="text-lg font-semibold text-gray-900">{team.name}</h1>
                <p className="text-sm text-gray-500">
                  {team.member_count} membre{team.member_count !== 1 ? 's' : ''} • Plan {team.plan}
                </p>
              </div>
            </div>
            
            <Button onClick={() => setShowInviteModal(true)}>
              <UserPlus className="w-4 h-4 mr-2" />
              Inviter
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-primary-50 rounded-lg">
                <Users className="w-6 h-6 text-primary-600" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Membres de l'équipe</h2>
                <p className="text-sm text-gray-500">Gérez les accès et les rôles</p>
              </div>
            </div>
          </div>

          {/* Members List */}
          <div className="divide-y divide-gray-100">
            {members.map((member) => {
              const RoleIcon = roleIcons[member.role] || Eye;
              
              return (
                <div key={member.id} className="p-4 flex items-center justify-between hover:bg-gray-50">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                      <span className="text-lg font-medium text-gray-600">
                        {member.username[0].toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900">
                          {member.full_name || member.username}
                        </span>
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${roleColors[member.role]}`}>
                          <RoleIcon className="w-3 h-3" />
                          {member.role}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500">{member.email}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <select
                      value={member.role}
                      onChange={(e) => handleUpdateRole(member.user_id, e.target.value)}
                      className="px-2 py-1 border border-gray-300 rounded text-sm"
                      disabled={member.role === 'owner'}
                    >
                      <option value="viewer">Viewer</option>
                      <option value="editor">Editor</option>
                      <option value="admin">Admin</option>
                    </select>
                    
                    {member.role !== 'owner' && (
                      <button
                        onClick={() => handleRemoveMember(member.user_id)}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </main>

      {/* Invite Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Inviter un membre</h3>
            
            <form onSubmit={handleInvite} className="space-y-4">
              <Input
                label="Email"
                type="email"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="collegue@entreprise.com"
                required
              />
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Rôle</label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="viewer">Viewer - Consultation uniquement</option>
                  <option value="editor">Editor - Peut modifier les documents</option>
                  <option value="admin">Admin - Gestion des membres</option>
                </select>
              </div>
              
              <div className="flex gap-3 pt-4">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => setShowInviteModal(false)}
                  className="flex-1"
                >
                  Annuler
                </Button>
                <Button type="submit" isLoading={isInviting} className="flex-1">
                  Inviter
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeamPage;