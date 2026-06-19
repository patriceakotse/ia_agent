"""
Service d'intégration avec OpenHands SDK.
Gère la communication avec le 'bras d'exécution' OpenHands.
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Callable, AsyncGenerator
from datetime import datetime
import httpx
from app.core.config import settings
from app.models.models import Session, Log, Feedback, Project


class OpenHandsService:
    """
    Service pour communiquer avec l'instance OpenHands.
    Supporte deux modes:
    1. SDK local (import direct)
    2. API REST (instance distante)
    """
    
    def __init__(self):
        self.base_url = settings.OPENHANDS_URL
        self.api_key = settings.OPENHANDS_API_KEY
        self.sdk_available = False
        
        # Vérifier si le SDK est disponible
        try:
            # from openhands import OpenHands
            # self.sdk_available = True
            pass
        except ImportError:
            self.sdk_available = False
    
    def _get_headers(self) -> Dict[str, str]:
        """Retourne les headers pour les requêtes API."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def write_specs_to_volume(self, project_id: int, documents: Dict[str, str], base_path: str = "/workspace") -> str:
        """
        Écrit les documents validés dans le volume partagé.
        Retourne le chemin du projet sur le volume.
        """
        project_path = f"{base_path}/project-{project_id}/specs"
        
        # Création du répertoire
        os.makedirs(project_path, exist_ok=True)
        
        # Écriture de chaque document
        for doc_type, content in documents.items():
            filename = f"{doc_type}.md"
            filepath = os.path.join(project_path, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Écriture du fichier de contexte principal
        context_file = os.path.join(project_path, "CONTEXT.md")
        with open(context_file, 'w', encoding='utf-8') as f:
            f.write("# Contexte du Projet\n\n")
            f.write(f"Project ID: {project_id}\n")
            f.write(f"Généré le: {datetime.now().isoformat()}\n\n")
            f.write("---\n\n")
            for doc_type, content in documents.items():
                f.write(f"\n## {doc_type.upper()}\n\n")
                f.write(content)
                f.write("\n\n---\n")
        
        return project_path
    
    async def create_session(self, project_id: int, specs_path: str) -> str:
        """
        Crée une nouvelle session OpenHands.
        Retourne l'ID de session.
        """
        if self.sdk_available:
            return await self._create_session_via_sdk(project_id, specs_path)
        else:
            return await self._create_session_via_api(project_id, specs_path)
    
    async def _create_session_via_api(self, project_id: int, specs_path: str) -> str:
        """Crée une session via l'API REST."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/api/sessions",
                headers=self._get_headers(),
                json={
                    "project_id": project_id,
                    "workspace_path": specs_path,
                    "instructions": self._generate_instructions(specs_path)
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("session_id", "")
    
    async def _create_session_via_sdk(self, project_id: int, specs_path: str) -> str:
        """Crée une session via le SDK OpenHands."""
        # Cette implémentation dépend de l'API exacte du SDK OpenHands
        # Placeholder pour l'instant
        raise NotImplementedError("SDK integration not yet implemented")
    
    def _generate_instructions(self, specs_path: str) -> str:
        """Génère les instructions pour OpenHands."""
        return f"""
Tu vas développer une application complète basée sur les spécifications situées dans {specs_path}.

Instructions:
1. Lis attentivement tous les fichiers .md dans {specs_path}
2. Analyse le cahier des charges (SPECS.md)
3. Implémente le code source complet
4. Écris des tests unitaires
5. Vérifie que tout compile et que les tests passent

Règles:
- Respecte les technologies et contraintes définies
- Code propre, documenté et testé
- Signale tout problème ou ambiguïté
- Fais un commit à chaque étape majeure

Après chaque tâche importante, fais un rapport d'avancement.
"""
    
    async def get_session_status(self, session_id: str) -> Dict:
        """Récupère le statut d'une session."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/api/sessions/{session_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def send_feedback(self, session_id: str, feedback: str) -> Dict:
        """Envoie un feedback à la session OpenHands."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/api/sessions/{session_id}/feedback",
                headers=self._get_headers(),
                json={"content": feedback}
            )
            response.raise_for_status()
            return response.json()
    
    async def stream_logs(self, session_id: str) -> AsyncGenerator[Dict, None]:
        """Stream les logs d'une session en temps réel."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "GET",
                f"{self.base_url}/api/sessions/{session_id}/logs/stream",
                headers=self._get_headers()
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            yield {"message": line, "level": "INFO"}
    
    async def stop_session(self, session_id: str) -> bool:
        """Arrête une session en cours."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/sessions/{session_id}/stop",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return True
            except Exception as e:
                print(f"Erreur lors de l'arrêt de session: {e}")
                return False
    
    def generate_deep_link(self, session_id: str) -> str:
        """Génère un lien profond vers la session OpenHands."""
        return f"{self.base_url}/session/{session_id}"


# Instance singleton
openhands_service = OpenHandsService()


async def launch_openhands_for_project(
    project: Project,
    documents: Dict[str, str],
    on_log: Optional[Callable] = None
) -> Dict:
    """
    Lance OpenHands pour un projet avec les documents validés.
    
    Args:
        project: Le projet à développer
        documents: Dict {doc_type: content}
        on_log: Callback optionnel pour recevoir les logs
    
    Returns:
        Dict avec session_id, deep_link, etc.
    """
    # 1. Écrire les specs sur le volume
    specs_path = await openhands_service.write_specs_to_volume(
        project.id,
        documents
    )
    
    # 2. Créer une session OpenHands
    session_id = await openhands_service.create_session(
        project.id,
        specs_path
    )
    
    # 3. Démarrer le streaming des logs en arrière-plan
    if on_log:
        asyncio.create_task(_stream_logs_background(session_id, on_log))
    
    # 4. Retourner les informations de connexion
    return {
        "session_id": session_id,
        "deep_link": openhands_service.generate_deep_link(session_id),
        "specs_path": specs_path,
        "status": "running"
    }


async def _stream_logs_background(session_id: str, on_log: Callable):
    """Background task pour streamer les logs."""
    try:
        async for log in openhands_service.stream_logs(session_id):
            await on_log(log)
    except Exception as e:
        print(f"Erreur dans le stream des logs: {e}")