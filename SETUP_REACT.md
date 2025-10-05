# 🚀 Setup React + Docker - Cluedo Custom v3

## ✅ Ce qui est fait

### Backend
- ✅ `backend/main.py` - API FastAPI complète
- ✅ `backend/defaults.py` - 3 thèmes prédéfinis (classic, office, fantasy)
- ✅ `backend/models.py`, `game_engine.py`, `game_manager.py` - Logique métier
- ✅ `backend/requirements.txt` - Dépendances Python

### Frontend (structure)
- ✅ `frontend/package.json` - Config React + Vite + Tailwind
- ✅ `frontend/vite.config.js` - Config Vite avec proxy API
- ✅ `frontend/tailwind.config.js` - Theme sombre
- ✅ `frontend/src/api.js` - Client API

## 📋 Ce qu'il reste à faire

### 1. Créer les composants React

Créer ces fichiers dans `frontend/src/` :

#### `main.jsx`
```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

#### `App.jsx`
```jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Join from './pages/Join'
import Game from './pages/Game'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gradient-to-br from-dark-950 via-dark-900 to-dark-950">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/join" element={<Join />} />
          <Route path="/game/:gameId/:playerId" element={<Game />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App
```

#### `pages/Home.jsx` - Page d'accueil
- Bouton "Créer une partie" (thème classic par défaut)
- Input nom du joueur
- Lien vers "Rejoindre une partie"

#### `pages/Join.jsx` - Rejoindre une partie
- Input code de partie (4 caractères)
- Input nom du joueur
- Bouton rejoindre

#### `pages/Game.jsx` - Interface de jeu
- Plateau avec positions
- Cartes du joueur
- Actions (Dés, Suggestion, Accusation, Passer)
- Historique
- Bouton "Démarrer" (si créateur et 3+ joueurs)

### 2. Créer le Dockerfile

```dockerfile
# Stage 1: Build frontend
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.11-slim
WORKDIR /app

# Install backend deps
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend/ ./backend/

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Expose port for Hugging Face
EXPOSE 7860

# Start server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
```

### 3. Créer docker-compose.yml (pour test local)

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "7860:7860"
    volumes:
      - ./backend:/app/backend
      - ./frontend/dist:/app/frontend/dist
    environment:
      - PYTHONUNBUFFERED=1
```

### 4. Créer README.md pour Hugging Face

```yaml
---
title: Cluedo Custom
emoji: 🔍
colorFrom: red
colorTo: purple
sdk: docker
pinned: false
app_port: 7860
---

# 🔍 Cluedo Custom

Créez votre propre jeu de Cluedo avec des suspects, armes et lieux personnalisés !

## 🎮 Comment jouer

1. **Créer une partie** : Choisissez un thème (Manoir classique, Bureau, Château)
2. **Partager le code** : Envoyez le code à 4 caractères à vos amis
3. **Jouer** : Lancez les dés, déplacez-vous, faites des suggestions !

## 🛠️ Développement local

\`\`\`bash
# Build et lancer avec Docker
docker-compose up --build

# Ou séparément :
# Backend
cd backend && pip install -r requirements.txt && uvicorn main:app --port 8000

# Frontend
cd frontend && npm install && npm run dev
\`\`\`
```

### 5. Commandes pour tester

```bash
# 1. Installer frontend
cd frontend
npm install

# 2. Builder frontend
npm run build

# 3. Tester backend seul (sert le frontend builded)
cd ../backend
pip install -r requirements.txt
uvicorn main:app --port 7860

# Ouvrir http://localhost:7860

# 4. Build Docker
cd ..
docker build -t cluedo-custom .
docker run -p 7860:7860 cluedo-custom

# 5. Deploy sur Hugging Face
# - Créer un nouveau Space (SDK: Docker)
# - Push le code
# - Hugging Face va build automatiquement
```

## 🎨 Templates de composants React simplifiés

Les composants doivent être **ultra-simples** :

### Home.jsx (minimal)
- Titre "Cluedo Custom"
- Input "Votre nom"
- Bouton "Créer une partie"
- Lien "Rejoindre une partie existante"

### Game.jsx (minimal)
- Section "Plateau" : Liste des pièces avec icônes joueurs
- Section "Mes cartes" : Liste simple
- Section "Actions" :
  - Si mon tour : Bouton "Lancer dés" OU "Passer"
  - Si déplacé : Selects (suspect/arme/pièce) + "Suggérer" / "Accuser"
- Section "Historique" : 5 dernières actions

## ⚡ Quick Start (après avoir créé les composants)

```bash
# Terminal 1 - Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 2 - Frontend (dev mode)
cd frontend
npm install
npm run dev
# Ouvre http://localhost:3000

# Pour production (single server)
cd frontend
npm run build
cd ../backend
uvicorn main:app --port 7860
# Ouvre http://localhost:7860
```

## 🐳 Déployer sur Hugging Face

1. Créer un Space : https://huggingface.co/new-space
2. Choisir SDK: **Docker**
3. Cloner le repo du Space
4. Copier tous les fichiers dedans
5. Ajouter `README.md` avec le header YAML
6. Push:
```bash
git add .
git commit -m "Initial commit"
git push
```

7. Attendre le build (~5-10 min)
8. Votre jeu est en ligne ! 🎉

---

**Note** : Les composants React sont volontairement simplifiés pour aller vite. Tu pourras les améliorer après le déploiement.
