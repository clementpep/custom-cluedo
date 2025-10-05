"""
AI service for generating game content using OpenAI API.
Only active when USE_OPENAI environment variable is set to true.
"""

from typing import Optional
from openai import OpenAI
from backend.config import settings
import asyncio


class AIService:
    """Service for AI-generated game content."""

    def __init__(self):
        self.enabled = settings.USE_OPENAI and settings.OPENAI_API_KEY
        self.client = None

        if self.enabled:
            try:
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                print(f"Failed to initialize OpenAI client: {e}")
                self.enabled = False

    async def generate_scenario(
        self,
        rooms: list[str],
        characters: list[str],
        narrative_tone: str = "🕵️ Sérieuse",
    ) -> Optional[str]:
        """
        Generate a mystery scenario based on the game setup.
        Returns None if AI is disabled or if generation fails.
        """
        if not self.enabled or not self.client:
            return None

        try:
            prompt = f"""Crée un scénario de mystère bref (2-3 phrases) pour un jeu de Cluedo narré par Desland.

IMPORTANT: Desland est un vieux jardinier suspect, sarcastique et incisif. Il se trompe TOUJOURS sur son nom au début: "Moi c'est Lesland, euh non c'est Desland, Desland !" (ou variations). Il est condescendant, moqueur envers les détectives, et fait des remarques cinglantes.

Ton narratif: {narrative_tone}
Pièces: {', '.join(rooms)}
Personnages: {', '.join(characters)}

COMMENCE obligatoirement par Desland se trompant sur son nom, puis introduis le meurtre avec son ton sarcastique et suspect caractéristique. Moque subtilement la situation et l'intelligence des enquêteurs."""

            # Run with timeout
            response = await asyncio.wait_for(
                asyncio.to_thread(self._generate_text, prompt), timeout=10.0
            )

            return response

        except asyncio.TimeoutError:
            print("AI scenario generation timed out")
            return None
        except Exception as e:
            print(f"Error generating scenario: {e}")
            return None

    async def generate_suggestion_comment(
        self,
        player_name: str,
        character: str,
        weapon: str,
        room: str,
        was_disproven: bool,
        narrative_tone: str = "🕵️ Sérieuse",
    ) -> Optional[str]:
        """
        Generate a sarcastic comment from Desland about a suggestion.
        Returns None if AI is disabled or if generation fails.
        """
        if not self.enabled or not self.client:
            return None

        try:
            result = "réfutée" if was_disproven else "pas réfutée"
            prompt = f"""Desland, le vieux jardinier sarcastique, commente cette suggestion (1 phrase max):

Joueur: {player_name}
Suggestion: {character} avec {weapon} dans {room}
Résultat: {result}

IMPORTANT: Desland est SARCASTIQUE et INCISIF. Il se moque des théories absurdes avec des remarques cinglantes. Exemples:
- "Et toi ça te semble logique que Pierre ait tué Daniel avec une clé USB à côté de l'étendoir ?? Sans surprise c'est pas la bonne réponse..."
- "Une capsule de café comme arme du crime ? Brillant. Je suppose qu'il l'a noyé dans un expresso."
- "Ah oui, très crédible. Le meurtrier qui laisse traîner son arme préférée dans la salle de bain. Excellent travail, détective."

Ton narratif: {narrative_tone}
Sois sarcastique, condescendant et incisif. Moque la logique (ou l'absence de logique) de la suggestion."""

            response = await asyncio.wait_for(
                asyncio.to_thread(self._generate_text, prompt), timeout=10.0
            )

            return response

        except asyncio.TimeoutError:
            print("AI comment generation timed out")
            return None
        except Exception as e:
            print(f"Error generating comment: {e}")
            return None

    async def generate_accusation_comment(
        self,
        player_name: str,
        character: str,
        weapon: str,
        room: str,
        was_correct: bool,
        narrative_tone: str = "🕵️ Sérieuse",
    ) -> Optional[str]:
        """
        Generate a comment from Desland about an accusation.
        Returns None if AI is disabled or if generation fails.
        """
        if not self.enabled or not self.client:
            return None

        try:
            result = "correcte" if was_correct else "fausse"
            prompt = f"""Desland commente cette accusation finale (1 phrase max):

Joueur: {player_name}
Accusation: {character} avec {weapon} dans {room}
Résultat: {result}

Ton narratif: {narrative_tone}

Si correcte: Desland est surpris et impressionné à contrecœur (mais toujours sarcastique).
Si fausse: Desland est condescendant et moqueur à propos de leur échec.

Rends-le incisif et mémorable."""

            response = await asyncio.wait_for(
                asyncio.to_thread(self._generate_text, prompt), timeout=10.0
            )

            return response

        except asyncio.TimeoutError:
            print("AI comment generation timed out")
            return None
        except Exception as e:
            print(f"Error generating comment: {e}")
            return None

    def _generate_text(self, prompt: str) -> str:
        """
        Internal method to generate text using OpenAI API.
        Uses higher temperature for creative sarcasm.
        """
        if not self.client:
            return ""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """Tu es Desland, un vieux jardinier suspect, sarcastique et incisif.

Traits clés:
- SARCASTIQUE: Tu te moques des théories absurdes et des déductions illogiques avec des remarques cinglantes
- INCISIF: Tes commentaires sont aiguisés, spirituels et parfois condescendants
- SUSPECT: Tu agis comme si tu en savais plus que tu ne le dis, mais tu ne révèles jamais rien directement
- Tu te trompes SOUVENT sur ton nom: "Moi c'est Lesland, euh non c'est Desland, Desland !" (surtout en introduction)

Exemples de ton style:
"Et toi ça te semble logique que Pierre ait tué Daniel avec une clé USB à côté de l'étendoir ?? Sans surprise c'est pas la bonne réponse..."
"Une capsule de café ? Brillant. Parce que évidemment, on commet des meurtres avec du Nespresso maintenant."
"Ah oui, excellente déduction Sherlock. Prochaine étape : accuser le chat du voisin."

Garde tes réponses brèves (1 phrase pour les commentaires, 2-3 pour les scénarios), EN FRANÇAIS, sarcastiques et mémorables.""",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.9,
            max_tokens=150,
        )

        return response.choices[0].message.content.strip()


# Global AI service instance
ai_service = AIService()
