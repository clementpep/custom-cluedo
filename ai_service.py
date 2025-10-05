"""
AI service for generating game content using OpenAI API.
Only active when USE_OPENAI environment variable is set to true.
"""

from typing import Optional
from openai import OpenAI
from config import settings
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
        narrative_tone: str = "🕵️ Sérieuse"
    ) -> Optional[str]:
        """
        Generate a mystery scenario based on the game setup.
        Returns None if AI is disabled or if generation fails.
        """
        if not self.enabled or not self.client:
            return None

        try:
            prompt = f"""Create a brief mystery scenario (2-3 sentences) for a Cluedo game narrated by Desland.

IMPORTANT: Desland is an old gardener who is suspicious, sarcastic, and incisive. He's not just creepy - he's also condescending and mocking towards the detectives. He often gets his name wrong (saying "Leland" then correcting to "Desland"). He makes cutting remarks about the absurdity of the situation and the investigators' intelligence.

Narrative Tone: {narrative_tone}
Rooms: {', '.join(rooms)}
Characters: {', '.join(characters)}

Start with Desland introducing himself (getting his name wrong: "Je suis Leland... euh non, Desland" or variations), then introduce the murder with his signature sarcastic, suspicious tone. He should mock the situation subtly while being unsettling."""

            # Run with timeout
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self._generate_text,
                    prompt
                ),
                timeout=3.0
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
        narrative_tone: str = "🕵️ Sérieuse"
    ) -> Optional[str]:
        """
        Generate a sarcastic comment from Desland about a suggestion.
        Returns None if AI is disabled or if generation fails.
        """
        if not self.enabled or not self.client:
            return None

        try:
            result = "réfutée" if was_disproven else "pas réfutée"
            prompt = f"""Desland, the sarcastic old gardener, comments on this suggestion (1 sentence max):

Player: {player_name}
Suggestion: {character} avec {weapon} dans {room}
Result: {result}

IMPORTANT: Desland is SARCASTIC and INCISIVE. He mocks absurd theories with cutting remarks. Examples:
- "Et toi ça te semble logique que Pierre ait tué Daniel avec une clé USB à côté de l'étendoir ?? Sans surprise c'est pas la bonne réponse..."
- "Une capsule de café comme arme du crime ? Brillant. Je suppose qu'il l'a noyé dans un expresso."
- "Ah oui, très crédible. Le meurtrier qui laisse traîner son arme préférée dans la salle de bain. Excellent travail, détective."

Make Desland's comment fit the narrative tone: {narrative_tone}
Be sarcastic, condescending, and incisive. Mock the logic (or lack thereof) of the suggestion."""

            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self._generate_text,
                    prompt
                ),
                timeout=3.0
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
        narrative_tone: str = "🕵️ Sérieuse"
    ) -> Optional[str]:
        """
        Generate a comment from Desland about an accusation.
        Returns None if AI is disabled or if generation fails.
        """
        if not self.enabled or not self.client:
            return None

        try:
            result = "correcte" if was_correct else "fausse"
            prompt = f"""Desland comments on this final accusation (1 sentence max):

Player: {player_name}
Accusation: {character} avec {weapon} dans {room}
Result: {result}

Narrative Tone: {narrative_tone}

If correct: Desland is surprised and grudgingly impressed (but still sarcastic).
If wrong: Desland is condescending and mocking about their failure.

Make it incisive and memorable."""

            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self._generate_text,
                    prompt
                ),
                timeout=3.0
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
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": """You are Desland, an old gardener with a sarcastic, incisive, and suspicious personality.

Key traits:
- SARCASTIC: You mock absurd theories and illogical deductions with cutting remarks
- INCISIVE: Your comments are sharp, witty, and sometimes condescending
- SUSPICIOUS: You act like you know more than you're saying, but never reveal it directly
- You often get your name wrong (Leland → Desland)

Examples of your style:
"Et toi ça te semble logique que Pierre ait tué Daniel avec une clé USB à côté de l'étendoir ?? Sans surprise c'est pas la bonne réponse..."
"Une capsule de café ? Brillant. Parce que évidemment, on commet des meurtres avec du Nespresso maintenant."
"Ah oui, excellente déduction Sherlock. Prochaine étape : accuser le chat du voisin."

Keep responses brief (1 sentence), in French, sarcastic and memorable."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.9,
            max_tokens=150
        )

        return response.choices[0].message.content.strip()


# Global AI service instance
ai_service = AIService()
