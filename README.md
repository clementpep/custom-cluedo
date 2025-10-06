---
title: Cluedo Custom - Real-World Mystery Game
emoji: 🔍
colorFrom: red
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
tags:
  - gradio
  - fastapi
  - game
  - multiplayer
  - cluedo
  - mystery
  - python
  - pydantic
  - openai
---

# 🕯️ Cluedo Custom - Jeu de Mystère Personnalisable

Application web de Cluedo personnalisable avec narrateur IA sarcastique (Desland, le vieux jardinier). Transformez votre environnement réel en plateau de jeu interactif !

## ✨ Fonctionnalités

- ✅ **Plateau de jeu personnalisable** - Disposez vos salles sur une grille avec drag & drop
- ✅ **Grille d'enquête interactive** - Cochez les possibilités éliminées (✅ Mes cartes, ❌ Éliminé, ❓ Peut-être)
- ✅ **Système de dés et déplacement** - Déplacez-vous sur le plateau circulaire
- ✅ **Suggestions et accusations** - Mécaniques de jeu Cluedo complètes
- ✅ **Narrateur IA Desland** - Commentaires sarcastiques en temps réel sur vos actions
- ✅ **Interface immersive** - Thème hanté avec animations et effets visuels
- ✅ **Multi-joueurs** - 3-8 joueurs, synchronisation en temps réel
- ✅ **Thèmes prédéfinis** - Classique (Manoir), Bureau, Fantastique

## 🚀 Démarrage Rapide

### Avec Docker (Recommandé)

```bash
# Build l'image
docker build -t custom-cluedo .

# Option 1: Lance sans IA (Desland désactivé)
docker run -p 7860:7860 custom-cluedo

# Option 2: Avec IA Desland activée (variables d'environnement)
docker run -p 7860:7860 \
  -e USE_OPENAI=true \
  -e OPENAI_API_KEY=your_key_here \
  custom-cluedo

# Option 3: Avec IA Desland activée (fichier .env)
# 1. Créer un fichier .env avec vos variables (voir .env.example)
# 2. Lancer avec --env-file
docker run -p 7860:7860 --env-file .env custom-cluedo

# Accéder à l'application
# Navigateur: http://localhost:7860
```

**⚠️ IMPORTANT pour l'IA** : Si vous voulez les commentaires sarcastiques de Desland, vous DEVEZ passer les variables d'environnement au conteneur Docker (option 2 ou 3).

### Développement Local

#### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev  # Dev server on http://localhost:5173
npm run build  # Build for production
```

### Déploiement Hugging Face Spaces

1. **Créer un nouveau Space**
   - SDK: **Docker**
   - Port: **7860**

2. **Variables d'environnement** (Settings → Variables):
   ```
   USE_OPENAI=true
   OPENAI_API_KEY=<votre_clé>
   ```

3. **Push le code**
   ```bash
   git push
   ```

## ⚙️ Configuration

| Variable | Description | Défaut |
|----------|-------------|--------|
| `USE_OPENAI` | Active le narrateur IA Desland | `false` |
| `OPENAI_API_KEY` | Clé API OpenAI (si USE_OPENAI=true) | `""` |
| `MAX_PLAYERS` | Nombre max de joueurs | `8` |
| `MIN_PLAYERS` | Nombre min de joueurs | `3` |

## 🎮 Comment Jouer

### 1. Créer une Partie

1. Entrez votre nom
2. Cliquez sur **"🚪 Entrer dans le Manoir"**
3. Un code de partie est généré (ex: `CBSB`)
4. Partagez ce code avec vos amis

### 2. Rejoindre une Partie

1. Cliquez sur **"👻 Rejoindre une partie existante"**
2. Entrez le code de partie
3. Entrez votre nom
4. Rejoignez !

### 3. Démarrer le Jeu

- Minimum **3 joueurs** requis
- Le créateur clique sur **"🚀 Commencer l'enquête"**
- Les cartes sont distribuées automatiquement

### 4. Jouer Votre Tour

Quand c'est votre tour :

1. **🎲 Lancer les dés** - Déplacez-vous sur le plateau
2. **💬 Suggérer** - Proposez un suspect + arme + salle
   - Les autres joueurs tentent de réfuter
3. **⚠️ Accuser** - Accusation finale (éliminé si faux !)
4. **📋 Grille d'enquête** - Notez vos déductions
   - Cliquez pour marquer : ✅ → ❌ → ❓ → ⬜

### 5. Gagner

- Premier à faire une accusation correcte gagne
- Ou dernier joueur non-éliminé

## 🤖 Narrateur IA : Desland

Activez `USE_OPENAI=true` pour les commentaires sarcastiques de Desland !

### Personnalité de Desland

> *"Je suis Leland... euh non, Desland. Le vieux jardinier de ce manoir maudit."*

- **Sarcastique** - Se moque des théories absurdes
- **Incisif** - Commentaires tranchants et condescendants
- **Suspicieux** - Semble en savoir plus qu'il ne dit
- **Confus** - Se trompe souvent de nom (Leland → Desland)

### Exemples de Commentaires

```
"Et toi ça te semble logique que Pierre ait tué Daniel avec une clé USB
à côté de l'étendoir ?? Sans surprise c'est pas la bonne réponse..."

"Une capsule de café ? Brillant. Parce que évidemment, on commet des
meurtres avec du Nespresso maintenant."

"Ah oui, excellente déduction Sherlock. Prochaine étape : accuser le
chat du voisin."
```

### Configuration IA

- Modèle: gpt-5-nano
- Température: 0.9 (créativité élevée)
- Timeout: 3 secondes max
- Fallback gracieux si indisponible

## 📁 Structure du Projet

```
custom-cluedo/
├── backend/
│   ├── main.py           # API FastAPI + Serving frontend
│   ├── models.py         # Modèles Pydantic (Game, Player, Cards...)
│   ├── game_engine.py    # Logique du jeu (règles, vérifications)
│   ├── game_manager.py   # Gestion des parties (CRUD)
│   ├── defaults.py       # Thèmes prédéfinis
│   ├── config.py         # Configuration
│   └── requirements.txt  # Dépendances Python
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.jsx  # Accueil + création partie
│   │   │   ├── Join.jsx  # Rejoindre partie
│   │   │   └── Game.jsx  # Interface de jeu
│   │   ├── components/
│   │   │   ├── GameBoard.jsx          # Plateau de jeu
│   │   │   ├── InvestigationGrid.jsx  # Grille d'enquête
│   │   │   └── AINavigator.jsx        # Narrateur Desland
│   │   └── api.js        # Client API
│   ├── package.json
│   └── tailwind.config.js
├── ai_service.py         # Service IA (Desland)
├── Dockerfile            # Build multi-stage
└── README.md
```

## 🔌 API Endpoints

### Parties
- `GET /api/health` - Santé de l'API
- `POST /api/games/quick-create` - Créer partie rapide
- `POST /api/games/join` - Rejoindre partie
- `POST /api/games/{game_id}/start` - Démarrer
- `GET /api/games/{game_id}/state/{player_id}` - État du jeu

### Actions
- `POST /api/games/{game_id}/roll` - Lancer dés
- `POST /api/games/{game_id}/suggest` - Suggestion
- `POST /api/games/{game_id}/accuse` - Accusation
- `POST /api/games/{game_id}/pass` - Passer tour

### Autres
- `GET /api/themes` - Thèmes disponibles

## 🛠️ Technologies

- **Backend** : FastAPI, Python 3.11, Pydantic
- **Frontend** : React 18, Vite, TailwindCSS
- **IA** : OpenAI gpt-5-nano (optionnel)
- **Stockage** : JSON (games.json)
- **Déploiement** : Docker, Hugging Face Spaces

## 🎨 Thèmes Disponibles

### Classique - Meurtre au Manoir 🏰
- **Suspects** : Mme Leblanc, Col. Moutarde, Mlle Rose, Prof. Violet, Mme Pervenche, M. Olive
- **Armes** : Poignard, Revolver, Corde, Chandelier, Clé anglaise, Poison
- **Salles** : Cuisine, Salon, Bureau, Chambre, Garage, Jardin

### Bureau - Meurtre au Bureau 💼
- **Suspects** : Claire, Pierre, Daniel, Marie, Thomas, Sophie
- **Armes** : Clé USB, Agrafeuse, Câble HDMI, Capsule de café, Souris, Plante verte
- **Salles** : Open Space, Salle de réunion, Cafétéria, Bureau CEO, Toilettes, Parking

### Fantastique - Meurtre au Château 🧙
- **Suspects** : Merlin le Sage, Dame Morgane, Chevalier Lancelot, Elfe Aranelle, Nain Thorin, Sorcière Malva
- **Armes** : Épée enchantée, Potion empoisonnée, Grimoire maudit, Dague runique, Bâton magique, Amulette sombre
- **Salles** : Grande Salle, Tour des Mages, Donjon, Bibliothèque, Armurerie, Crypte

## 📝 Licence

Projet personnel - Usage libre pour l'éducation et le divertissement

## 🎯 Crédits

- Jeu basé sur le Cluedo classique
- Interface immersive avec thème hanté
- Narrateur IA Desland créé avec amour et sarcasme 👻
