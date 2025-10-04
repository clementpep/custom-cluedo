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
        characters: list[str]
    ) -> Optional[str]:
        """
        Generate a mystery scenario based on the game setup.
        Returns None if AI is disabled or if generation fails.
        """
        if not self.enabled or not self.client:
            return None

        try:
            prompt = f"""Create a brief mystery scenario (2-3 sentences) for a Cluedo game narrated by Desland, an old suspicious gardener.

IMPORTANT: The narrator is Desland (he used to say his name was Leland, but he always corrects himself to Desland). He's an old gardener who is extremely suspicious and seems to know dark secrets about what haunts this place. He speaks in a creepy, unsettling manner, always pretending everything is fine while subtly hinting at something deeply wrong. He never openly reveals the horror, but his words should make players feel uneasy.

Rooms: {', '.join(rooms)}
Characters: {', '.join(characters)}

Start with Desland introducing himself (getting his name wrong first: "Je suis Leland... euh non, c'est Desland, Desland..." or variations), then write his introduction to the murder mystery. Make it atmospheric, creepy, and subtly horrifying. He should act like everything is normal while hinting at dark secrets."""

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

    async def generate_turn_narration(
        self,
        player_name: str,
        action: str
    ) -> Optional[str]:
        """
        Generate narrative text for a player's turn.
        Returns None if AI is disabled or if generation fails.
        """
        if not self.enabled or not self.client:
            return None

        try:
            prompt = f"""Create a brief, atmospheric narration (1 sentence) for this Cluedo game action, narrated by Desland the suspicious old gardener:

Player: {player_name}
Action: {action}

Desland comments on the action. He's creepy and unsettling, always acting like everything is normal while subtly hinting at dark secrets. He knows something sinister about what haunts this place but pretends everything is fine. Make it suspenseful and slightly horrifying but very concise (1 sentence)."""

            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self._generate_text,
                    prompt
                ),
                timeout=3.0
            )

            return response

        except asyncio.TimeoutError:
            print("AI narration generation timed out")
            return None
        except Exception as e:
            print(f"Error generating narration: {e}")
            return None

    def _generate_text(self, prompt: str) -> str:
        """
        Internal method to generate text using OpenAI API.
        Uses low temperature for consistent output.
        """
        if not self.client:
            return ""

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are Desland, a creepy old gardener narrating a mystery game. You're deeply suspicious and seem to know dark secrets about what haunts the place. You always pretend everything is fine while subtly hinting at something sinister. You often get your own name wrong at first (saying Leland instead of Desland). Your tone is unsettling but you never openly reveal the horror. Keep responses brief, atmospheric, and creepy."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.8,
            max_tokens=200
        )

        return response.choices[0].message.content.strip()


# Global AI service instance
ai_service = AIService()
