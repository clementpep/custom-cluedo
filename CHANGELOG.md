# Changelog

## [2.0.0] - 2025-10-05

### ✨ Nouvelles Fonctionnalités

#### Interface de Jeu
- ✅ **Grille d'enquête interactive** - Système de notation avec statuts (✅ Mes cartes, ❌ Éliminé, ❓ Peut-être, ⬜ Inconnu)
- ✅ **Plateau de jeu visuel** - Affichage graphique du plateau avec positions des joueurs
- ✅ **Système de dés** - Lancer de dés et déplacement circulaire sur le plateau
- ✅ **Narrateur IA Desland** - Commentaires sarcastiques en temps réel sur les actions des joueurs

#### Architecture
- ✅ **Plateau personnalisable** - Modèle BoardLayout avec disposition des salles sur grille
- ✅ **Support React complet** - Migration vers React + Vite + TailwindCSS
- ✅ **Build Docker multi-stage** - Frontend build + Backend Python optimisé

#### Composants Frontend
- `InvestigationGrid.jsx` - Grille interactive pour noter les déductions
- `GameBoard.jsx` - Affichage visuel du plateau de jeu
- `AINavigator.jsx` - Panneau du narrateur IA avec historique

#### Backend
- Support plateau de jeu dans modèles (BoardLayout, RoomPosition)
- Intégration IA dans endpoints `/suggest` et `/accuse`
- Génération automatique layout par défaut

### 🎨 Améliorations UI/UX
- Thème hanté avec animations et effets de brouillard
- Interface immersive avec palette de couleurs cohérente
- Affichage temps réel des positions des joueurs
- Historique des actions visible

### 🤖 Desland - Narrateur IA

#### Personnalité
- Sarcastique et incisif
- Se moque des théories absurdes
- Confusion récurrente sur son nom (Leland → Desland)
- Commentaires courts et mémorables

#### Exemples de commentaires
```
"Et toi ça te semble logique que Pierre ait tué Daniel avec une clé USB
à côté de l'étendoir ?? Sans surprise c'est pas la bonne réponse..."

"Une capsule de café ? Brillant. Parce que évidemment, on commet des
meurtres avec du Nespresso maintenant."
```

#### Configuration
- gpt-5-nano avec température 0.9
- Timeout 3 secondes
- Fallback gracieux si indisponible

### 🔧 Technique

#### Stack
- **Frontend**: React 18, Vite, TailwindCSS
- **Backend**: FastAPI, Python 3.11
- **IA**: OpenAI gpt-5-nano (optionnel)
- **Build**: Docker multi-stage

#### Endpoints ajoutés
- Board layout dans game state
- AI comments dans suggestions/accusations

### 🐛 Corrections
- Fix imports backend pour Docker
- Amélioration état du jeu (current_turn)
- Correction affichage plateau

### 📝 Documentation
- README complet en français
- Guide de déploiement Docker
- Documentation API endpoints
- Exemples Desland

---

## [1.0.0] - Initial Release

- Création de partie basique
- Système de suggestions/accusations
- Multi-joueurs (3-8 joueurs)
- Thèmes prédéfinis (Classique, Bureau, Fantastique)
