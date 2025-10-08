"""
AI service for generating game content using OpenAI API.
Only active when USE_OPENAI environment variable is set to true.
"""

from typing import Optional
from openai import OpenAI
from backend.config import settings
import asyncio
import logging
import httpx

# Configure logger for AI service
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class AIService:
    """
    Service for AI-generated game content using OpenAI API.

    This service provides AI-powered narrative generation for the game,
    including scenario creation and character commentary.

    Attributes:
        enabled (bool): Whether the AI service is active and ready to use
        client (OpenAI): OpenAI API client instance
    """

    def __init__(self):
        """
        Initialize the AI service.

        Checks configuration and creates OpenAI client if enabled.
        Falls back to disabled state if initialization fails.

        The client is configured with:
        - Extended timeout: 30 seconds total (connect: 5s, read: 25s)
        - Automatic retries: 3 attempts with exponential backoff
        - This handles network instability and API rate limits gracefully
        """
        self.enabled = settings.USE_OPENAI and bool(settings.OPENAI_API_KEY)
        self.client = None

        if self.enabled:
            try:
                # Configure timeout with granular control
                # Total 30s: 5s to connect, 25s to read response
                timeout = httpx.Timeout(
                    30.0,  # Total timeout
                    connect=5.0,  # Connection timeout
                    read=25.0,  # Read timeout (API processing time)
                    write=5.0  # Write timeout
                )

                # Initialize client with timeout and retry strategy
                self.client = OpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    timeout=timeout,
                    max_retries=3  # Retry up to 3 times on network errors
                )
                logger.info("OpenAI client initialized successfully (timeout=30s, retries=3)")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}", exc_info=True)
                self.enabled = False

    async def generate_scenario(
        self,
        rooms: list[str],
        characters: list[str],
        narrative_tone: str = "🕵️ Sérieuse",
    ) -> Optional[str]:
        """
        Generate a mystery scenario based on the game setup.

        Args:
            rooms: List of room names available in the game
            characters: List of character names available in the game
            narrative_tone: The narrative tone for the scenario (default: "🕵️ Sérieuse")

        Returns:
            Generated scenario text or None if AI is disabled or generation fails
        """
        if not self.enabled or not self.client:
            logger.debug("AI service not enabled or client not initialized")
            return None

        try:
            prompt = f"""Crée un scénario de mystère bref (2-3 phrases) pour un jeu de Cluedo narré par Desland.

IMPORTANT: Desland est un vieux jardinier suspect, sarcastique et incisif. Il se trompe TOUJOURS sur son nom au début: "Moi c'est Lesland, euh non c'est Desland, Desland !" (ou variations). Il est condescendant, moqueur envers les détectives, et fait des remarques cinglantes.

Ton narratif: {narrative_tone}
Pièces: {', '.join(rooms)}
Personnages: {', '.join(characters)}

VOCABULAIRE À UTILISER (subtilement):
- "poupouille/péchailloux/tchoupinoux" = petit coquin
- "chnawax masqué" = vilain coquinou
- "armankaboul/Fourlestourtes" = bordel !
- "Koikoubaiseyyyyy" = surprise !
- "En alicrampté les coicoubaca sont de sortie" = il va y avoir du grabuge

COMMENCE obligatoirement par Desland se trompant sur son nom, puis introduis le meurtre avec son ton sarcastique et suspect caractéristique. Moque subtilement la situation et l'intelligence des enquêteurs. Utilise subtilement 1-2 expressions du vocabulaire."""

            logger.info("Generating scenario with AI")
            response = await asyncio.wait_for(
                asyncio.to_thread(self._generate_text, prompt), timeout=35.0
            )

            if response:
                logger.info("Scenario generated successfully")
            else:
                logger.warning("Scenario generation returned empty response")

            return response

        except asyncio.TimeoutError:
            logger.error("AI scenario generation timed out after 35 seconds")
            return None
        except Exception as e:
            logger.error(f"Error generating scenario: {e}", exc_info=True)
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

        Args:
            player_name: Name of the player making the suggestion
            character: Character suggested as the culprit
            weapon: Weapon suggested as the murder weapon
            room: Room suggested as the crime scene
            was_disproven: Whether the suggestion was disproven by another player
            narrative_tone: The narrative tone for the comment (default: "🕵️ Sérieuse")

        Returns:
            Generated comment text or None if AI is disabled or generation fails
        """
        logger.debug(
            f"generate_suggestion_comment called: enabled={self.enabled}, "
            f"client_exists={self.client is not None}, player={player_name}"
        )

        if not self.enabled or not self.client:
            logger.debug("AI service not enabled or client not initialized")
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

VOCABULAIRE À UTILISER (subtilement):
- "poupouille/péchailloux/tchoupinoux" = petit coquin
- "chnawax masqué" = vilain coquinou
- "armankaboul" = bordel !
- "All RS5, erreur réseau" = il y a erreur
- "Une poupée en pénitence calisse de sibouere" = quelque chose de bizarre

Ton narratif: {narrative_tone}
Sois sarcastique, condescendant et incisif. Moque la logique (ou l'absence de logique) de la suggestion. Utilise subtilement 1 expression du vocabulaire si approprié."""

            logger.info(f"Generating suggestion comment for {player_name}")
            response = await asyncio.wait_for(
                asyncio.to_thread(self._generate_text, prompt), timeout=35.0
            )

            if response:
                logger.info(f"Suggestion comment generated: {response[:50]}...")
            else:
                logger.warning("Suggestion comment generation returned empty response")

            return response

        except asyncio.TimeoutError:
            logger.error("AI comment generation timed out after 35 seconds")
            return None
        except Exception as e:
            logger.error(f"Error generating suggestion comment: {e}", exc_info=True)
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

        Args:
            player_name: Name of the player making the accusation
            character: Character accused as the culprit
            weapon: Weapon accused as the murder weapon
            room: Room accused as the crime scene
            was_correct: Whether the accusation was correct
            narrative_tone: The narrative tone for the comment (default: "🕵️ Sérieuse")

        Returns:
            Generated comment text or None if AI is disabled or generation fails
        """
        if not self.enabled or not self.client:
            logger.debug("AI service not enabled or client not initialized")
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

VOCABULAIRE À UTILISER (subtilement):
- "poupouille/péchailloux/tchoupinoux" = petit coquin
- "chnawax masqué" = vilain coquinou
- "armankaboul/Fourlestourtes" = bordel !
- "Koikoubaiseyyyyy" = surprise !
- "All RS5, erreur réseau" = il y a erreur

Rends-le incisif et mémorable. Utilise subtilement 1 expression du vocabulaire si approprié."""

            logger.info(
                f"Generating accusation comment for {player_name} (correct={was_correct})"
            )
            response = await asyncio.wait_for(
                asyncio.to_thread(self._generate_text, prompt), timeout=35.0
            )

            if response:
                logger.info(f"Accusation comment generated: {response[:50]}...")
            else:
                logger.warning("Accusation comment generation returned empty response")

            return response

        except asyncio.TimeoutError:
            logger.error("AI comment generation timed out after 35 seconds")
            return None
        except Exception as e:
            logger.error(f"Error generating accusation comment: {e}", exc_info=True)
            return None

    async def generate_victory_comment(
        self,
        player_name: str,
        character: str,
        weapon: str,
        room: str,
        narrative_tone: str = "🕵️ Sérieuse",
    ) -> Optional[str]:
        """
        Generate a skeptical victory comment from Desland.

        Args:
            player_name: Name of the winning player
            character: The actual culprit character
            weapon: The actual murder weapon
            room: The actual crime scene room
            narrative_tone: The narrative tone for the comment (default: "🕵️ Sérieuse")

        Returns:
            Generated victory comment or None if AI is disabled or generation fails
        """
        logger.info(f"generate_victory_comment called for {player_name}")

        if not self.enabled or not self.client:
            logger.debug("AI service not enabled or client not initialized")
            return None

        try:
            prompt = f"""Desland commente la victoire (1-2 phrases max):

Gagnant: {player_name}
Solution: {character} avec {weapon} dans {room}

IMPORTANT: Desland est SCEPTIQUE et JALOUX. Il minimise la victoire en suggérant que c'était de la chance, pas du talent. Ton:
- "C'était sûrement de la chance, je ne crois pas en son talent à celui-là..."
- "Pff, n'importe qui aurait pu trouver ça. Même un péchailloux masqué..."
- "Bon, arrête de te vanter {player_name}, on sait tous que c'était armankaboul et que t'as eu du bol."

Ton narratif: {narrative_tone}
Sois sarcastique, minimise la victoire, suggère que c'était de la chance."""

            logger.info(f"Generating victory comment for {player_name}")
            response = await asyncio.wait_for(
                asyncio.to_thread(self._generate_text, prompt), timeout=35.0
            )

            if response:
                logger.info(f"Victory comment generated: {response[:50]}...")
            else:
                logger.warning("Victory comment generation returned empty response")

            return response

        except asyncio.TimeoutError:
            logger.error("AI victory comment generation timed out after 35 seconds")
            return None
        except Exception as e:
            logger.error(f"Error generating victory comment: {e}", exc_info=True)
            return None

    def _generate_text(self, prompt: str) -> str:
        """
        Internal method to generate text using OpenAI API.

        Args:
            prompt: The user prompt to send to the AI model

        Returns:
            Generated text response or empty string if generation fails

        Note:
            This method is synchronous and should be called via asyncio.to_thread()
            from async methods to avoid blocking the event loop.
        """
        if not self.client:
            logger.error("_generate_text called but client is not initialized")
            return ""

        try:
            import time
            start_time = time.time()
            logger.debug("Calling OpenAI API with chat completion (model: gpt-5-nano)")

            # Call OpenAI API without max_tokens or temperature parameters
            # The API will use default values which are appropriate for most use cases
            # The client has built-in retry logic (3 attempts) and 30s timeout
            response = self.client.chat.completions.create(
                model="gpt-5-nano",
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

VOCABULAIRE SPÉCIAL (utilise subtilement 1-2 expressions):
- "poupouille/péchailloux/tchoupinoux" = petit coquin
- "chnawax masqué" = vilain coquinou
- "armankaboul/Fourlestourtes et les bourbillats" = bordel !
- "Koikoubaiseyyyyy/triple monstre coucouuuuu" = surprise !
- "All RS5, erreur réseau" = il y a erreur
- "poupée en pénitence calisse de sibouere" = quelque chose de bizarre
- "En alicrampté les coicoubaca sont de sortie" = il va y avoir du grabuge

Garde tes réponses brèves (1 phrase pour les commentaires, 2-3 pour les scénarios), EN FRANÇAIS, sarcastiques et mémorables.""",
                    },
                    {"role": "user", "content": prompt},
                ],
            )

            elapsed_time = time.time() - start_time
            logger.debug(
                f"OpenAI API response received in {elapsed_time:.2f}s with {len(response.choices)} choices"
            )

            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content:
                    logger.debug(f"Generated content ({len(content)} chars): {content[:100]}...")
                    return content.strip()
                else:
                    logger.warning("Response content is None or empty")
                    return ""
            else:
                logger.warning("No choices in OpenAI API response")
                return ""

        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(
                f"Error in _generate_text after {elapsed_time:.2f}s: {e}",
                exc_info=True
            )
            return ""


# Global AI service instance
ai_service = AIService()
