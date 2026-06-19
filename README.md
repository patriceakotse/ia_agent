# Agent Orchestrator

**Plateforme SaaS d'Orchestration de Développement Pilotée par IA**

Transformez vos compte-rendus de réunions clients en applications fonctionnelles, automatiquement.

---

## 🎯 Vue d'ensemble

Agent Orchestrator automatise le cycle de vie complet d'un projet logiciel :

1. **Saisie** → Entrez le compte-rendu de votre réunion client
2. **Analyse IA** → Des agents spécialisés analysent et génèrent les documents de cadrage
3. **Validation** → Éditez et validez les documents générés
4. **Implémentation** → OpenHands génère le code automatiquement
5. **Monitoring** → Surveillez et itérez en temps réel

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        LE CERVEAU                                │
│                    (Dashboard Web)                               │
│  - Interface React + TypeScript                                  │
│  - API FastAPI + PostgreSQL                                      │
│  - Génération de documents IA (CrewAI/LangChain)                 │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              │ API / SDK
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     LE BRAS D'EXÉCUTION                          │
│                   (Instance OpenHands)                           │
│  - Génération de code source                                     │
│  - Tests automatisés                                             │
│  - Itérations intelligentes                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Installation

### Prérequis

- Docker & Docker Compose
- Clés API OpenAI et/ou Anthropic

### Démarrage rapide

```bash
# Cloner le repository
git clone <votre-repo>
cd agent-orchestrator

# Configurer les variables d'environnement
cp .env.example .env
# Éditez .env et ajoutez vos clés API

# Lancer avec Docker Compose
docker-compose up -d
```

L'application sera accessible sur :
- **Frontend** : http://localhost:5173
- **API** : http://localhost:8000
- **Documentation API** : http://localhost:8000/docs
- **OpenHands** : http://localhost:3000

---

## 📁 Structure du projet

```
agent-orchestrator/
├── backend/                    # API FastAPI
│   ├── app/
│   │   ├── api/               # Routes API
│   │   ├── agents/            # Agents IA de génération
│   │   ├── core/              # Configuration
│   │   ├── models/            # Modèles SQLAlchemy
│   │   ├── schemas/           # Schémas Pydantic
│   │   └── services/          # Services métier
│   └── requirements.txt
│
├── frontend/                   # Application React
│   ├── src/
│   │   ├── components/        # Composants UI
│   │   ├── pages/             # Pages de l'application
│   │   ├── services/          # Appels API
│   │   ├── store/             # État global (Zustand)
│   │   └── types/             # Types TypeScript
│   └── package.json
│
├── workspace/                  # Volume partagé avec OpenHands
│   └── project-{id}/
│       └── specs/             # Documents validés
│
├── docker-compose.yml
├── README.md
└── prd-agent-orchestrator.md  # Spécifications détaillées
```

---

## 📝 Documents générés

L'IA génère automatiquement les documents suivants :

| Document | Description |
|----------|-------------|
| `README.md` | Vue d'ensemble du projet et objectifs |
| `SPECS.md` | Cahier des charges technique complet |
| `DB_SCHEMA.md` | Modèle Conceptuel de Données (MCD) |
| `TASKS.md` | User Stories et tâches priorisées |
| `WORKFLOW.md` | Processus métier et diagrammes |
| `MARKETING.md` | Stratégie marketing et KPIs |

---

## 🔧 Développement local

### Backend

```bash
cd backend

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate   # Windows

# Installer les dépendances
pip install -r requirements.txt

# Lancer le serveur de développement
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Installer les dépendances
npm install

# Lancer le serveur de développement
npm run dev
```

---

## 🔐 Configuration

### Variables d'environnement (.env)

```env
# Application
APP_NAME=Agent Orchestrator
SECRET_KEY=votre-cle-secrete-tres-longue

# Base de données
DATABASE_URL=sqlite:///./agent_orchestrator.db

# IA (au moins une requise)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# OpenHands
OPENHANDS_URL=http://localhost:3000
```

---

## 🧪 Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm run test
```

---

## 📄 Licence

MIT License

---

## 🤝 Contribution

Les contributions sont les bienvenues ! Veuillez lire les directives de contribution avant de soumettre une PR.

---

<div align="center">
  <strong>Construit avec ❤️ pour automatiser le développement logiciel</strong>
</div>