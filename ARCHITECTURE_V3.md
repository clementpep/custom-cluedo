# 🏗️ Architecture v3.0 - React + FastAPI + Docker

## 🎯 Objectif
Interface simple et intuitive, déployable sur Hugging Face Spaces via Docker.

## 📐 Architecture

```
custom-cluedo/
├── backend/              # FastAPI
│   ├── main.py          # API principale
│   ├── models.py        # Modèles Pydantic
│   ├── game_engine.py   # Logique métier
│   ├── game_manager.py  # Gestion parties
│   └── requirements.txt
│
├── frontend/            # React
│   ├── public/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   ├── Join.jsx
│   │   │   └── Game.jsx
│   │   ├── components/
│   │   │   ├── Board.jsx
│   │   │   ├── PlayerCards.jsx
│   │   │   └── ActionPanel.jsx
│   │   └── api.js
│   ├── package.json
│   └── vite.config.js
│
├── Dockerfile           # Multi-stage build
├── docker-compose.yml   # Dev local
└── README.md
```

## 🎮 Flux Simplifié

### 1. Création (Valeurs par Défaut)
```
Titre: "Meurtre au Manoir"
Tonalité: "Thriller"
Lieux: ["Cuisine", "Salon", "Bureau", "Chambre", "Garage", "Jardin"]
Armes: ["Poignard", "Revolver", "Corde", "Chandelier", "Clé anglaise", "Poison"]
Suspects: ["Mme Leblanc", "Col. Moutarde", "Mlle Rose", "Prof. Violet", "Mme Pervenche", "M. Olive"]
```

**Personnalisation optionnelle** (accordéon replié par défaut)

### 2. Interface de Jeu

**Layout simple :**
```
┌─────────────────────────────────────┐
│  Cluedo Custom - Code: AB7F         │
├─────────────────────────────────────┤
│                                     │
│  [Plateau avec positions]           │
│                                     │
├─────────────────────────────────────┤
│  Vos cartes: [🃏] [🃏] [🃏]        │
├─────────────────────────────────────┤
│  Tour de: Alice                     │
│  [🎲 Lancer dés] ou [⏭️ Passer]    │
│                                     │
│  Si déplacé:                        │
│  [💭 Suggérer] [⚡ Accuser]        │
└─────────────────────────────────────┘
```

## 🐳 Docker pour Hugging Face

### Dockerfile
```dockerfile
# Stage 1: Build frontend
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Run backend + serve frontend
FROM python:3.11-slim
WORKDIR /app

# Install backend deps
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend/ ./backend/

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Expose port
EXPOSE 7860

# Start FastAPI (serves both API and static frontend)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
```

## 🚀 Déploiement Hugging Face

### README.md du Space
```yaml
---
title: Cluedo Custom
emoji: 🔍
colorFrom: red
colorTo: purple
sdk: docker
pinned: false
---
```

## ⚙️ Configuration FastAPI pour Servir React

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# API routes
@app.get("/api/health")
async def health():
    return {"status": "ok"}

# ... autres routes API ...

# Serve React app
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")

@app.get("/{full_path:path}")
async def serve_react(full_path: str):
    return FileResponse("frontend/dist/index.html")
```

## 📦 Valeurs par Défaut

### Thèmes Prédéfinis
```python
DEFAULT_THEMES = {
    "classic": {
        "name": "Meurtre au Manoir",
        "rooms": ["Cuisine", "Salon", "Bureau", "Chambre", "Garage", "Jardin"],
        "weapons": ["Poignard", "Revolver", "Corde", "Chandelier", "Clé anglaise", "Poison"],
        "suspects": ["Mme Leblanc", "Col. Moutarde", "Mlle Rose", "Prof. Violet", "Mme Pervenche", "M. Olive"]
    },
    "office": {
        "name": "Meurtre au Bureau",
        "rooms": ["Open Space", "Salle de réunion", "Cafétéria", "Bureau CEO", "Toilettes", "Parking"],
        "weapons": ["Clé USB", "Agrafeuse", "Câble", "Capsule café", "Souris", "Plante"],
        "suspects": ["Claire", "Pierre", "Daniel", "Marie", "Thomas", "Sophie"]
    }
}
```

## 🎨 Design Simple (TailwindCSS)

- **Palette** : Tons sombres mystérieux
- **Composants** : shadcn/ui ou Chakra UI
- **Animations** : Framer Motion (minimales)

## 🔧 APIs Essentielles

```
POST   /api/games/create        # Créer (avec défauts)
POST   /api/games/join          # Rejoindre
POST   /api/games/{id}/start    # Démarrer
GET    /api/games/{id}/state    # État du jeu
POST   /api/games/{id}/roll     # Lancer dés
POST   /api/games/{id}/suggest  # Suggestion
POST   /api/games/{id}/accuse   # Accusation
POST   /api/games/{id}/pass     # Passer tour
```

## ✨ Fonctionnalités Simplifiées

### MVP (Version 1)
- ✅ Création avec valeurs par défaut
- ✅ Rejoindre avec code
- ✅ Déplacement avec dés
- ✅ Suggestions/Accusations
- ✅ Desland (commentaires simples, pas d'IA)

### Future (Version 2)
- [ ] IA avec OpenAI
- [ ] Personnalisation complète
- [ ] Thèmes multiples
- [ ] Animations avancées

---

**Cette architecture sera plus robuste, plus simple à utiliser et déployable facilement sur Hugging Face Spaces.**
