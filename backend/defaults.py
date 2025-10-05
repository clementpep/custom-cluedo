"""
Default game presets for quick setup
"""

DEFAULT_THEMES = {
    "classic": {
        "name": "Meurtre au Manoir",
        "tone": "🎬 Thriller",
        "rooms": [
            "Cuisine",
            "Salon",
            "Bureau",
            "Chambre",
            "Garage",
            "Jardin"
        ],
        "weapons": [
            "Poignard",
            "Revolver",
            "Corde",
            "Chandelier",
            "Clé anglaise",
            "Poison"
        ],
        "suspects": [
            "Mme Leblanc",
            "Col. Moutarde",
            "Mlle Rose",
            "Prof. Violet",
            "Mme Pervenche",
            "M. Olive"
        ]
    },
    "office": {
        "name": "Meurtre au Bureau",
        "tone": "😂 Parodique",
        "rooms": [
            "Open Space",
            "Salle de réunion",
            "Cafétéria",
            "Bureau CEO",
            "Toilettes",
            "Parking"
        ],
        "weapons": [
            "Clé USB",
            "Agrafeuse",
            "Câble HDMI",
            "Capsule de café",
            "Souris d'ordinateur",
            "Plante verte"
        ],
        "suspects": [
            "Claire",
            "Pierre",
            "Daniel",
            "Marie",
            "Thomas",
            "Sophie"
        ]
    },
    "fantasy": {
        "name": "Meurtre au Château",
        "tone": "🧙‍♂️ Fantastique",
        "rooms": [
            "Grande Salle",
            "Tour des Mages",
            "Donjon",
            "Bibliothèque",
            "Armurerie",
            "Crypte"
        ],
        "weapons": [
            "Épée enchantée",
            "Potion empoisonnée",
            "Grimoire maudit",
            "Dague runique",
            "Bâton magique",
            "Amulette sombre"
        ],
        "suspects": [
            "Merlin le Sage",
            "Dame Morgane",
            "Chevalier Lancelot",
            "Elfe Aranelle",
            "Nain Thorin",
            "Sorcière Malva"
        ]
    }
}

# Default theme to use
DEFAULT_THEME = "classic"

def get_default_game_config(theme: str = DEFAULT_THEME):
    """Get default game configuration"""
    if theme not in DEFAULT_THEMES:
        theme = DEFAULT_THEME

    config = DEFAULT_THEMES[theme].copy()
    return config
