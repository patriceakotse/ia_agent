"""
Service d'intégration pour xAI (Grok)
"""

import httpx
from typing import List, Dict, Optional, Any
from app.core.config import settings


class XAIClient:
    """
    Client pour l'API x.ai (Grok)
    """
    
    BASE_URL = "https://api.x.ai/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.XAI_API_KEY
        self.base_url = settings.XAI_BASE_URL or self.BASE_URL
        
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "grok-4.3",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Génère une réponse en utilisant l'API x.ai.
        
        Args:
            messages: Liste des messages au format [{"role": "user", "content": "..."}]
            model: Modèle à utiliser (grok-4.3, grok-3, etc.)
            temperature: Température pour la génération (0.0 - 2.0)
            max_tokens: Nombre maximum de tokens à générer
            
        Returns:
            Dict contenant la réponse et les informations de facturation
        """
        if not self.api_key:
            raise ValueError("XAI_API_KEY n'est pas configuré")
        
        # Format x.ai pour l'API Responses
        payload = {
            "model": model,
            "input": messages,
        }
        
        if temperature:
            payload["temperature"] = temperature
            
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/responses",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def generate_document(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "grok-4.3",
    ) -> str:
        """
        Génère un document en utilisant Grok.
        
        Args:
            system_prompt: Instructions pour le système
            user_prompt: Requête utilisateur
            model: Modèle à utiliser
            
        Returns:
            Texte généré
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        result = await self.chat_completion(messages, model=model)
        
        # x.ai retourne la réponse dans output[0].content[0].text
        if "output" in result and len(result["output"]) > 0:
            for item in result["output"]:
                if isinstance(item, dict) and "content" in item:
                    for content in item["content"]:
                        if isinstance(content, dict) and "text" in content:
                            return content["text"]
        
        return str(result)
    
    async def analyze_meeting_notes(
        self,
        meeting_notes: str,
        document_type: str,
        model: str = "grok-4.3",
    ) -> str:
        """
        Analyse des notes de réunion et génère un document.
        
        Args:
            meeting_notes: Compte-rendu de la réunion
            document_type: Type de document à générer
            model: Modèle à utiliser
            
        Returns:
            Document généré en Markdown
        """
        prompts = {
            "readme": (
                "Tu es un expert en documentation technique. Génère un README.md complet et professionnel "
                "pour un projet logiciel basé sur les notes de réunion fournies. Utilise Markdown avec badges, "
                "sections claires et exemples de code si pertinent."
            ),
            "specs": (
                "Tu es un analyste fonctionnel expert. Génère un cahier des charges technique complet (SPECS.md) "
                "basé sur les notes de réunion. Inclus: objectifs, périmètre, exigences fonctionnelles et non-fonctionnelles, "
                "contraintes, risques et mitigations."
            ),
            "tasks": (
                "Tu es un Product Owner expert. Génère des User Stories détaillées et priorisées (TASKS.md) "
                "basé sur les notes de réunion. Utilise le format: En tant que [rôle], je veux [fonctionnalité], "
                "afin de [bénéfice]. Inclus critères d'acceptation."
            ),
            "db_schema": (
                "Tu es un expert en base de données. Génère un modèle conceptuel de données complet (DB_SCHEMA.md) "
                "avec des diagrammes Mermaid. Inclus: entités, attributs, relations, types de données et contraintes."
            ),
            "workflow": (
                "Tu es un expert en processus métier. Génère une documentation de workflow (WORKFLOW.md) "
                "avec des diagrammes Mermaid. Inclus: flowchart du processus, étapes clés, rôles impliqués, "
                "points de décision et exceptions."
            ),
            "marketing": (
                "Tu es un expert marketing digital. Génère une stratégie marketing complète (MARKETING.md) "
                "basée sur les notes de réunion. Inclus: analyse de marché, persona, positionnement, "
                "canaux, calendrier et KPIs."
            ),
        }
        
        system_prompt = prompts.get(document_type, prompts["specs"])
        
        user_prompt = f"""
Notes de réunion:
---
{meeting_notes}
---

Génère le document {document_type}.md correspondant.
"""
        
        return await self.generate_document(system_prompt, user_prompt, model)


# Instance singleton
xai_client = XAIClient()


# Modèles disponibles chez x.ai
XAI_MODELS = [
    {"id": "grok-4.3", "name": "Grok 4.3", "description": "Modèle le plus puissant"},
    {"id": "grok-4", "name": "Grok 4", "description": "Modèle haute performance"},
    {"id": "grok-3", "name": "Grok 3", "description": "Modèle équilibré"},
    {"id": "grok-3-fast", "name": "Grok 3 Fast", "description": "Réponse rapide"},
    {"id": "grok-2", "name": "Grok 2", "description": "Modèle stable"},
    {"id": "grok-2-fast", "name": "Grok 2 Fast", "description": "Rapide et efficace"},
]


# Prix par 1M tokens (approximatifs)
XAI_PRICING = {
    "grok-4.3": {"input": 3.0, "output": 15.0},
    "grok-4": {"input": 3.0, "output": 15.0},
    "grok-3": {"input": 1.0, "output": 5.0},
    "grok-3-fast": {"input": 0.5, "output": 2.5},
    "grok-2": {"input": 0.5, "output": 2.5},
    "grok-2-fast": {"input": 0.25, "output": 1.25},
}
