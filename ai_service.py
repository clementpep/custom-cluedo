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
            prompt = f"""Create a brief mystery scenario (2-3 sentences) for a Cluedo game.

Rooms: {', '.join(rooms)}
Characters: {', '.join(characters)}

Write an engaging introduction that sets up the murder mystery in this location. Keep it concise and atmospheric."""

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
            prompt = f"""Create a brief, atmospheric narration (1 sentence) for this Cluedo game action:
Player: {player_name}
Action: {action}

Make it suspenseful and engaging but very concise."""

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
                    "content": "You are a creative writer for mystery games. Keep responses brief and atmospheric."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=150
        )

        return response.choices[0].message.content.strip()


# Global AI service instance
ai_service = AIService()
