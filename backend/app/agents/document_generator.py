"""
Agents IA pour la génération automatique de documents de cadrage.
Utilise CrewAI pour orchestrer plusieurs agents spécialisés.
"""

import os
import re
from typing import Dict, List, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from app.core.config import settings


# Configuration du LLM
def get_llm():
    if settings.ANTHROPIC_API_KEY:
        return ChatAnthropic(
            model="claude-3-sonnet-20240229",
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            temperature=settings.LLM_TEMPERATURE
        )
    elif settings.OPENAI_API_KEY:
        return ChatOpenAI(
            model=settings.LLM_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=settings.LLM_TEMPERATURE
        )
    else:
        raise ValueError("Aucun LLM configuré. Définissez OPENAI_API_KEY ou ANTHROPIC_API_KEY")


# Prompts système pour chaque type de document
SYSTEM_PROMPTS = {
    "readme": """Tu es un expert en rédaction de documentation technique.
Ton rôle est de générer un README.md complet et professionnel pour un projet logiciel.
Le README doit inclure:
- Description du projet
- Objectifs business
- Fonctionnalités principales
- Stack technique utilisée
- Instructions d'installation
- Structure du projet

Sois concis mais complet. Utilise le format Markdown.
Retourne UNIQUEMENT le contenu du README.md, sans explanation préalable.""",

    "specs": """Tu es un expert en analyse fonctionnelle et cahier des charges.
Ton rôle est de générer un SPECS.md (Spécifications Techniques) complet.
Le document doit inclure:
- Vue d'ensemble du système
- Fonctionnalités détaillées avec critères d'acceptation
- Contraintes techniques
- Exigences non fonctionnelles (performance, sécurité, disponibilité)
- Hypothèses et dépendances
- Glossaire des termes métier

Sois précis et exhaustif. Utilise le format Markdown avec des tableaux quand pertinent.
Retourne UNIQUEMENT le contenu du SPECS.md.""",

    "db_schema": """Tu es un expert en modélisation de bases de données.
Ton rôle est de générer un DB_SCHEMA.md décrivant le modèle conceptuel de données (MCD).
Le document doit inclure:
- Diagramme MCD en syntaxe PlantUML ou Mermaid
- Liste des entités avec leurs attributs
- Relations entre entités (1:1, 1:N, N:N)
- Types de données recommandés
- Contraintes d'intégrité
- Index recommandés

Utilise la syntaxe Mermaid pour le diagramme ER.
Retourne UNIQUEMENT le contenu du DB_SCHEMA.md.""",

    "tasks": """Tu es un expert en gestion de projet et méthodologies agiles.
Ton rôle est de générer un TASKS.md avec les user stories et tâches.
Le document doit inclure:
- Épics (grands lots de fonctionnalités)
- User stories au format: EN TANT QUE... JE VEUX... AFIN DE...
- Critères d'acceptation pour chaque user story
- Priorisation (MoSCoW: Must, Should, Could, Won't)
- Dépendances entre tâches
- Estimation de complexité (Fibonacci)

Sois exhaustif et organises les stories par domaine fonctionnel.
Retourne UNIQUEMENT le contenu du TASKS.md.""",

    "marketing": """Tu es un expert en stratégie marketing digitale.
Ton rôle est de générer un MARKETING_STRATEGY.md complet.
Le document doit inclure:
- Positionnement marché
- Persona client idéal
- Proposition de valeur unique
- Canaux d'acquisition
- Stratégie de contenu
- KPIs et métriques de suivi
- Budget estimé par canal

Sois stratégique et orienté résultats.
Retourne UNIQUEMENT le contenu du MARKETING_STRATEGY.md.""",

    "workflow": """Tu es un expert en optimisation des processus métier.
Ton rôle est de générer un WORKFLOW.md décrivant les processus métier.
Le document doit inclure:
- Vue d'ensemble du processus principal
- Diagramme de flux (BPMN ou Mermaid)
- Description de chaque étape
- Acteurs impliqués
- Points de décision
- Exceptions et cas limites
- KPIs de processus

Utilise la syntaxe Mermaid pour les diagrammes de flux.
Retourne UNIQUEMENT le contenu du WORKFLOW.md."""
}


def extract_entities(text: str) -> Dict[str, List[str]]:
    """Extrait les entités clés du compte-rendu."""
    llm = get_llm()
    
    prompt = f"""Analyse ce compte-rendu de réunion et extrait:
1. Les noms des utilisateurs/acteurs mentionnés
2. Les fonctionnalités demandées
3. Les contraintes ou exigences mentionnées
4. Les outils/technologies suggérés
5. Les objectifs business

Compte-rendu:
---
{text}
---

Réponds au format JSON:
{{
    "actors": ["liste des acteurs"],
    "features": ["liste des fonctionnalités"],
    "constraints": ["liste des contraintes"],
    "technologies": ["liste des technologies"],
    "business_goals": ["liste des objectifs business"]
}}"""

    try:
        response = llm.invoke(prompt)
        # Parse JSON from response
        content = response.content if hasattr(response, 'content') else str(response)
        # Extract JSON block if present
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            import json
            return json.loads(json_match.group())
    except Exception as e:
        print(f"Error extracting entities: {e}")
    
    return {
        "actors": [],
        "features": [],
        "constraints": [],
        "technologies": [],
        "business_goals": []
    }


def generate_document(doc_type: str, meeting_notes: str, context: Optional[Dict] = None) -> str:
    """Génère un document spécifique."""
    if doc_type not in SYSTEM_PROMPTS:
        raise ValueError(f"Type de document inconnu: {doc_type}")
    
    llm = get_llm()
    system_prompt = SYSTEM_PROMPTS[doc_type]
    
    # Construction du prompt avec le contexte
    user_prompt = f"Compte-rendu de réunion:\n---\n{meeting_notes}\n---"
    
    if context:
        user_prompt += f"\n\nContexte additionnel:\n{context}"
    
    try:
        response = llm.invoke([
            ("system", system_prompt),
            ("human", user_prompt)
        ])
        return response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        raise Exception(f"Erreur lors de la génération du document {doc_type}: {str(e)}")


def generate_all_documents(meeting_notes: str) -> Dict[str, str]:
    """
    Génère tous les documents de cadrage à partir du compte-rendu.
    Retourne un dictionnaire {doc_type: content}
    """
    # Extraction préalable des entités pour enrichir le contexte
    entities = extract_entities(meeting_notes)
    
    documents = {}
    context = f"""
Contexte extrait automatiquement:
- Acteurs: {', '.join(entities.get('actors', []))}
- Fonctionnalités: {', '.join(entities.get('features', []))}
- Contraintes: {', '.join(entities.get('constraints', []))}
- Technologies: {', '.join(entities.get('technologies', []))}
- Objectifs business: {', '.join(entities.get('business_goals', []))}
"""
    
    # Ordre de génération optimisé (dépendances entre documents)
    doc_order = ["readme", "specs", "tasks", "db_schema", "workflow", "marketing"]
    
    for doc_type in doc_order:
        print(f"Génération du document: {doc_type}")
        try:
            documents[doc_type] = generate_document(doc_type, meeting_notes, context)
        except Exception as e:
            print(f"Erreur pour {doc_type}: {e}")
            documents[doc_type] = f"# Erreur de génération\n\nLe document n'a pas pu être généré: {str(e)}"
    
    return documents


def get_document_title(doc_type: str) -> str:
    """Retourne le titre du document selon son type."""
    titles = {
        "readme": "README - Vue d'ensemble",
        "specs": "SPECS - Cahier des charges technique",
        "db_schema": "DB_SCHEMA - Modèle de données",
        "tasks": "TASKS - User Stories et tâches",
        "marketing": "MARKETING - Stratégie marketing",
        "workflow": "WORKFLOW - Processus métier"
    }
    return titles.get(doc_type, doc_type.upper())


# Point d'entrée pour les tests
if __name__ == "__main__":
    sample_notes = """
    Réunion avec le client ACME Corp.
    
    Participants: Marie Dubois (Directrice Marketing), Jean-Pierre Martin (DSI)
    
    Le client souhaite une plateforme e-commerce pour vendre leurs produits artisanaux.
    
    Fonctionnalités demandées:
    - Catalogue produits avec photos et descriptions
    - Panier et checkout sécurisé
    - Paiement par carte bancaire et PayPal
    - Suivi des commandes
    - Espace client pour l'historique
    
    Contraintes:
    - Doit supporter 1000 utilisateurs simultanés
    - Temps de chargement < 2 secondes
    - Design responsive mobile-first
    - Conformité RGPD
    
    Technologies préférées: React, Node.js, PostgreSQL
    
    Budget: 50K€
    Délai: 3 mois
    """
    
    docs = generate_all_documents(sample_notes)
    for doc_type, content in docs.items():
        print(f"\n{'='*60}")
        print(f"DOCUMENT: {doc_type}")
        print(f"{'='*60}")
        print(content[:500] + "..." if len(content) > 500 else content)