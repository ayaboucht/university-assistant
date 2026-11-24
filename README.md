# Assistant intelligent pour la vie universitaire à l’EMSI

## Sujet

L'objectif de ce projet est de développer un assistant intelligent permettant aux étudiants d'obtenir rapidement des réponses à leurs questions concernant la vie universitaire à l’EMSI, les études et les procédures administratives.

L'application s'appuiera sur un ensemble de documents universitaires, tels que les règlements intérieurs, les guides pédagogiques, les procédures administratives, les plannings et les documents de formation. Grâce à une approche **Retrieval-Augmented Generation (RAG)**, les passages pertinents sont extraits du corpus documentaire puis transmis à un modèle de langage afin de fournir des réponses contextualisées, sourcées et fiables.

---

## Fonctionnalités principales

- **🔐 Authentification et rôles :** connexion sécurisée (compte académique Microsoft `@emsi-edu.ma` via OpenID Connect / JWT) avec gestion des accès côté backend selon le rôle (`student` ou `admin`).
- **📂 Gestion des documents :** permettre à un administrateur d'importer des documents universitaires au format PDF ou TXT, de suivre leur état d'indexation et de gérer le corpus.
- **💬 Assistant conversationnel :** permettre aux étudiants de poser des questions en langage naturel et d'obtenir des réponses adaptées.
- **🔎 Recherche intelligente :** retrouver automatiquement les passages les plus pertinents dans les documents grâce à la recherche sémantique vectorielle avant la génération.
- **📚 Affichage des sources :** présenter les documents, pages et extraits utilisés pour générer chaque réponse afin de faciliter la vérification des informations.
- **🕘 Historique des conversations :** conserver les échanges en base de données afin que les étudiants puissent consulter leurs questions et réponses précédentes après reconnexion.
- **🛡️ Réponses fiables :** lorsque les documents disponibles ne permettent pas de répondre de manière fiable à une question, l'assistant le signale explicitement plutôt que d'inventer une information.
- **⚙️ Automatisation & déploiement :** orchestration des services conteneurisés avec Docker Compose et automatisation de workflows via n8n.

---

## Architecture et pile technologique

| Couche | Technologies retenues | Rôle |
| :--- | :--- | :--- |
| **Interface utilisateur** | Streamlit | Pages de connexion, chatbot, historique et administration documentaire |
| **Backend API** | FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2, Alembic | Authentification (Microsoft Entra ID / JWT), contrôle des rôles, API REST |
| **Moteur RAG** | Extraction PDF/DOCX/TXT, embeddings multilingues (`sentence-transformers`), LLM | Découpage, vectorisation, recherche sémantique et génération sourcée |
| **Base de données** | PostgreSQL + extension `pgvector` | Persistance des utilisateurs, documents, conversations, messages et vecteurs |
| **Automatisation** | n8n | Workflows d'indexation automatique et/ou d'évaluation périodique |
| **Qualité & tests** | `pytest`, `ruff`, Playwright | Tests unitaires, d'intégration, de bout en bout et évaluation RAG |
| **Conteneurisation** | Docker, Docker Compose | Déploiement reproductible multi-services |

---

## Structure du dépôt

```text
university-assistant/
├── app.py                     # Point d'entrée de l'interface Streamlit
├── config/                    # Paramètres et configuration de l'application
├── data/
│   ├── raw/original_files/    # Corpus documentaire brut classé par catégorie
│   ├── processed/             # Données extraites / nettoyées
│   ├── index/                 # Index locaux / caches
│   └── reference/             # Inventaire du corpus (corpus_index.csv) et dictionnaire
├── docs/                      # Documentation technique, architecture et validation
├── notebooks/                 # Explorations et expérimentations RAG
├── scripts/
│   ├── audit_corpus.py        # Audit qualité du corpus (SHA-256, OCR, PII, CSV)
│   └── data_preparation.sh    # Script de préparation / indexation
├── src/
│   ├── ui/                    # Pages Streamlit (login, chat, admin_docs)
│   ├── document_processing/   # Chargement et chunking des documents
│   ├── embeddings/            # Génération des embeddings
│   ├── retrieval/             # Recherche de passages pertinents
│   ├── vector_store/          # Stockage vectoriel
│   ├── rag/                   # Chaîne RAG et génération sourcée
│   ├── database/              # Persistance et modèles
│   └── utils/                 # Utilitaires et journalisation
├── tests/
│   ├── qa_dataset.csv         # Jeu de questions/réponses pour l'évaluation et les tests
│   ├── unit/                  # Tests unitaires
│   └── integration/           # Tests d'intégration
├── .env.example               # Exemple des variables d'environnement requises
├── pyproject.toml             # Dépendances et configuration Python (ruff, pytest)
└── README.md
```

---

## Prérequis et démarrage local

### 1. Prérequis

- **Python** `>= 3.11, < 3.14` (cible recommandée : **Python 3.12**)
- **Git**
- **Docker** et **Docker Compose**

### 2. Installation

```bash
git clone https://github.com/ayaboucht/university-assistant.git
cd university-assistant

python -m venv .venv
# Linux / macOS :
source .venv/bin/activate
# Windows PowerShell :
.venv\Scripts\Activate.ps1

pip install -e ".[dev]"
```

### 3. Variables d'environnement

Copier le fichier d'exemple et renseigner les valeurs nécessaires :

```bash
cp .env.example .env
```

Principales variables définies dans [`.env.example`](.env.example) :

- **Base de données** : `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `DATABASE_URL`
- **Authentification & sécurité** : `ENV`, `JWT_SECRET_KEY`, `ALLOWED_DOMAINS`, `ADMIN_EMAILS`
- **Services & IA** : `API_URL`, `LLM_API_KEY`, `EMBEDDING_MODEL`, `N8N_WEBHOOK_URL`

> Ne jamais versionner le fichier `.env` ni aucune clé secrète dans le dépôt.

### 4. Lancer l'interface Streamlit (version actuelle)

```bash
streamlit run app.py
```

---

## Gestion et audit du corpus documentaire

Les documents collectés sont rangés dans `data/raw/original_files/` par thématique (`administration/`, `emplois/`, `encadrements/`, `pedagogie/`, `planning/`, `resultats/`).

Un script d'audit permet de contrôler la qualité du corpus et de maintenir l'inventaire [`data/reference/corpus_index.csv`](data/reference/corpus_index.csv) :

```bash
python scripts/audit_corpus.py
```

Ce script effectue automatiquement :
- la détection des **doublons exacts** par empreinte SHA-256 ;
- la vérification de l'**extractibilité du texte** (repérage des PDF scannés nécessitant un traitement OCR) ;
- la détection d'indices de **données personnelles** (e-mails, numéros de téléphone, CIN, listes nominatives) ;
- la mise à jour de `data/reference/corpus_index.csv` tout en préservant les annotations manuelles et les documents en attente (`a_demander`).

Pour afficher uniquement le rapport sans modifier le fichier CSV :

```bash
python scripts/audit_corpus.py --no-update-csv
```

---

## Tests et qualité du code

```bash
# Lancer les tests
pytest

# Vérifier le style et le formatage
ruff check .
```

---

## Convention Git

- `main` : branche principale stable et exécutable.
- `feature/*` : branches de développement (`feature/frontend`, `feature/backend`, `feature/rag`, `feature/devops`).
- Toute intégration dans `main` passe par une **Pull Request** relue par au moins un membre du projet.
