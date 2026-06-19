# PRD: Plateforme SaaS d'Orchestration de Développement Pilotée par IA

## 1. Introduction

### Objectif du Projet
Créer une plateforme web SaaS qui automatise le cycle de vie complet d'un projet logiciel, de la saisie du compte-rendu de réunion client jusqu'à la génération automatique du code source via OpenHands.

### Problème Résolu
- **Avant:** Les consultants doivent manually transformer des compte-rendus de réunions en spécifications techniques, puis coordonner avec des développeurs.
- **Après:** Un workflow automatisé où l'IA analyse, conçoit et génère du code prêt à l'emploi.

### Utilisateurs Cibles
- Consultants / Chefs de projet / Commerciaux
- Développeurs / Architectes

---

## 2. Architecture Technique

### Composants Principaux

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PLATEFORME SAAS                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────┐         ┌──────────────────────────────┐  │
│  │   LE CERVEAU         │         │    LE BRAS D'EXÉCUTION       │  │
│  │   (Dashboard Web)    │◄───────►│    (Instance OpenHands)      │  │
│  │                      │   API   │                              │  │
│  │  - Authentification  │   SDK   │  - Génération code           │  │
│  │  - Saisie besoins    │         │  - Écriture code             │  │
│  │  - Base données      │         │  - Exécution tests           │  │
│  │  - Interface UI      │         │  - Itérations                │  │
│  │  - Génération PRD    │         │                              │  │
│  └──────────────────────┘         └──────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Stack Technologique
- **Frontend:** React + TypeScript + TailwindCSS
- **Backend:** FastAPI (Python) + PostgreSQL
- **ORM:** SQLAlchemy / Prisma
- **Auth:** JWT + OAuth2
- **Agents IA:** CrewAI ou LangChain Agents
- **LLM:** OpenAI GPT-4 / Claude / Gemini
- **Exécution:** Docker + OpenHands SDK

---

## 3. User Stories

### US-001: Connexion et Authentification
**Description:** En tant qu'utilisateur, je veux me connecter à la plateforme pour accéder à mes projets en toute sécurité.

**Acceptance Criteria:**
- [ ] Formulaire de connexion avec email/mot de passe
- [ ] Inscription avec validation email
- [ ] JWT token stocké en session
- [ ] Déconnexion fonctionnelle
- [ ] Mot de passe oublié (email de réinitialisation)

---

### US-002: Création de Projet
**Description:** En tant qu'utilisateur, je veux créer un nouveau projet pour démarrer l'analyse d'un compte-rendu client.

**Acceptance Criteria:**
- [ ] Bouton "Nouveau Projet" visible sur le dashboard
- [ ] Formulaire avec champs: Nom du projet, Client, Description courte
- [ ] Projet créé et visible dans la liste
- [ ] Redirection vers la page de saisie du compte-rendu

---

### US-003: Saisie du Compte-Rendu
**Description:** En tant qu'utilisateur, je veux coller le compte-rendu brut de ma réunion pour lancer l'analyse IA.

**Acceptance Criteria:**
- [ ] Zone de texte面积 large (min 500px hauteur)
- [ ] Support du collage multi-lignes
- [ ] Compteur de caractères
- [ ] Bouton "Analyser et Générer"
- [ ] Sauvegarde automatique en brouillon

---

### US-004: Analyse IA et Génération de Documents
**Description:** En tant qu'utilisateur, je veux que l'IA analyse mon compte-rendu et génère automatiquement les documents de cadrage.

**Acceptance Criteria:**
- [ ] Indicateur de progression (stepper: Analyse → Génération → Validation)
- [ ] Génération de README.md (vue d'ensemble)
- [ ] Génération de SPECS.md (cahier des charges technique)
- [ ] Génération de DB_SCHEMA.md (MCD/Modèle de données)
- [ ] Génération de TASKS.md (User Stories priorisées)
- [ ] Tous les documents au format Markdown

---

### US-005: Édition et Validation des Documents
**Description:** En tant qu'utilisateur, je veux pouvoir modifier et valider chaque document avant l'implémentation.

**Acceptance Criteria:**
- [ ] Affichage des documents dans des onglets
- [ ] Éditeur Markdown avec prévisualisation
- [ ] Bouton "Valider" par document
- [ ] Bouton "Valider Tout" global
- [ ] Historique des modifications (versioning)

---

### US-006: Lancement d'OpenHands
**Description:** En tant qu'utilisateur, je veux lancer automatiquement OpenHands avec les documents validés pour démarrer le développement.

**Acceptance Criteria:**
- [ ] Bouton "Lancer OpenHands" après validation
- [ ] Écriture des fichiers dans /workspace/projet-client/specs/
- [ ] Génération d'un lien profond vers OpenHands
- [ ] Notification de démarrage de session

---

### US-007: Monitoring en Temps Réel
**Description:** En tant qu'utilisateur, je veux voir l'avancement d'OpenHands en temps réel.

**Acceptance Criteria:**
- [ ] Dashboard avec barres de progression
- [ ] Logs en streaming (websocket ou polling)
- [ ] Statuts: "Analyse", "Codage", "Tests", "Terminé"
- [ ] Timestamps pour chaque étape

---

### US-008: Feedback et Itérations
**Description:** En tant qu'utilisateur, je veux pouvoir envoyer des instructions correctives à OpenHands pendant l'exécution.

**Acceptance Criteria:**
- [ ] Champ de texte "Feedback" sur le dashboard
- [ ] Bouton "Envoyer à OpenHands"
- [ ] Intégration du feedback dans le contexte de l'agent
- [ ] Affichage de la réponse/acknowledgment

---

### US-009: Liste des Projets et Historique
**Description:** En tant qu'utilisateur, je veux voir tous mes projets et leur état d'avancement.

**Acceptance Criteria:**
- [ ] Grille/liste des projets avec cartes
- [ ] Indicateurs d'état (Brouillon, En cours, Terminé)
- [ ] Filtres par état et date
- [ ] Recherche par nom de projet
- [ ] Détails du projet accessible

---

## 4. Fonctionnalités Requises

### FR-1: Gestion des Projets
- FR-1.1: Créer un projet avec métadonnées
- FR-1.2: Lister les projets avec pagination
- FR-1.3: Modifier les informations du projet
- FR-1.4: Supprimer un projet (avec confirmation)
- FR-1.5: Exporter le projet en ZIP (documents + code)

### FR-2: Génération de Documents IA
- FR-2.1: Parser le compte-rendu avec NLP
- FR-2.2: Extraire les entités clés (utilisateurs, fonctionnalités, contraintes)
- FR-2.3: Générer README.md structuré
- FR-2.4: Générer SPECS.md complet
- FR-2.5: Générer DB_SCHEMA.md avec MCD
- FR-2.6: Générer TASKS.md avec user stories

### FR-3: Intégration OpenHands
- FR-3.1: Écrire les fichiers dans le volume partagé
- FR-3.2: Initialiser une session OpenHands via SDK
- FR-3.3: Transférer le contexte et les instructions
- FR-3.4: Recevoir les événements de progression
- FR-3.5: Gérer les erreurs et timeouts

### FR-4: Monitoring et Feedback
- FR-4.1: WebSocket pour logs en temps réel
- FR-4.2: Interface de feedback intégrée
- FR-4.3: Historique des interactions
- FR-4.4: Alertes en cas d'erreur

### FR-5: Sécurité et Authentification
- FR-5.1: Inscription et connexion sécurisé
- FR-5.2: JWT avec refresh token
- FR-5.3: Permissions par projet
- FR-5.4: Rate limiting
- FR-5.5: Logs d'audit

---

## 5. Hors Scope

- Génération de code sans validation humaine préalable
- Hébergement multi-tenant sur infrastructure personnalisée
- Intégration avec des outils tierces (Jira, GitHub) - V2
- Application mobile native
- Support hors ligne

---

## 6. Considérations UX/UI

### Design System
- Palette: Bleu principal (#2563EB), Accent (#10B981), Neutres
- Typographie: Inter pour le corps, Geist ou SF Pro pour les titres
- Espacement: Système 4px (4, 8, 12, 16, 24, 32, 48, 64)

### Layout Principal
```
┌────────────────────────────────────────────────────────────┐
│  Logo   [Projets]  [Nouveau]           [User] [Déconnexion]│
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─────────────────┐  ┌──────────────────────────────────┐│
│  │                 │  │                                  ││
│  │  Liste Projets  │  │     Contenu Principal            ││
│  │  (Sidebar)      │  │     (Dashboard/Editor)           ││
│  │                 │  │                                  ││
│  │                 │  │                                  ││
│  └─────────────────┘  └──────────────────────────────────┘│
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### États des Composants
- **Loading:** Skeleton + spinner
- **Empty:** Illustration + CTA
- **Error:** Message rouge + retry
- **Success:** Toast notification

---

## 7. Considérations Techniques

### API Endpoints
```
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/refresh

GET    /api/projects
POST   /api/projects
GET    /api/projects/:id
PUT    /api/projects/:id
DELETE /api/projects/:id

POST   /api/projects/:id/analyze
GET    /api/projects/:id/documents
PUT    /api/projects/:id/documents/:type
POST   /api/projects/:id/launch

GET    /api/projects/:id/sessions
GET    /api/projects/:id/logs
POST   /api/projects/:id/feedback

WS     /ws/projects/:id/stream
```

### Modèle de Données
```
User {
  id, email, password_hash, name, created_at
}

Project {
  id, user_id, name, client, description,
  meeting_notes, status, created_at, updated_at
}

Document {
  id, project_id, type, content, version, created_at
}

Session {
  id, project_id, status, started_at, ended_at
}

Log {
  id, session_id, level, message, timestamp
}
```

### Sécurité
- HTTPS obligatoire
- Hash des mots de passe (bcrypt/argon2)
- Validation des entrées (Pydantic/Zod)
- Protection CSRF
- CORS configuré

---

## 8. Métriques de Succès

| Métrique | Cible |
|----------|-------|
| Temps de génération des documents | < 2 minutes |
| Taux de satisfaction utilisateur | > 90% |
| Précision de l'analyse IA | > 85% |
| Temps de première réponse OpenHands | < 30 secondes |
| Uptime de la plateforme | > 99.5% |

---

## 9. Questions Ouvertes

1. **Quel LLM préféré?** OpenAI GPT-4, Anthropic Claude, ou Google Gemini?
2. **Multi-tenancy?** Un seul instance pour tous les utilisateurs ou isolation par organisation?
3. **Limites d'utilisation?** Rate limiting par utilisateur ou par organisation?
4. **Stockage du code généré?** Git interne ou export uniquement?
5. **Personnalisation des prompts?** L'utilisateur peut-il modifier les prompts d'analyse?

---

## 10. Livrables MVP

1. ✅ Dashboard web fonctionnel
2. ✅ Système d'authentification
3. ✅ Interface de saisie du compte-rendu
4. ✅ Pipeline de génération de documents IA
5. ✅ Éditeur Markdown avec validation
6. ✅ Intégration OpenHands via SDK
7. ✅ Console de monitoring en temps réel
8. ✅ Système de feedback