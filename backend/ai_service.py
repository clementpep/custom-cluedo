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
        self.enabled = settings.USE_OPENAI and bool(settings.OPENAI_API_KEY)
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

VOCABULAIRE À UTILISER (subtilement):
- "poupouille/péchailloux/tchoupinoux" = petit coquin
- "chnawax masqué" = vilain coquinou
- "armankaboul/Fourlestourtes" = bordel !
- "Koikoubaiseyyyyy" = surprise !
- "En alicrampté les coicoubaca sont de sortie" = il va y avoir du grabuge

COMMENCE obligatoirement par Desland se trompant sur son nom, puis introduis le meurtre avec son ton sarcastique et suspect caractéristique. Moque subtilement la situation et l'intelligence des enquêteurs. Utilise subtilement 1-2 expressions du vocabulaire."""

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
        print(
            f"[AI Service] generate_suggestion_comment called: enabled={self.enabled}, client={self.client is not None}"
        )

        if not self.enabled or not self.client:
            print(f"[AI Service] AI disabled or client not initialized")
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

            print(f"[AI Service] Calling OpenAI API...")
            response = await asyncio.wait_for(
                asyncio.to_thread(self._generate_text, prompt), timeout=10.0
            )
            print(f"[AI Service] OpenAI response received: {response}")

            return response

        except asyncio.TimeoutError:
            print("[AI Service] AI comment generation timed out")
            return None
        except Exception as e:
            import traceback

            print(f"[AI Service] Error generating comment: {e}")
            print(traceback.format_exc())
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

VOCABULAIRE À UTILISER (subtilement):
- "poupouille/péchailloux/tchoupinoux" = petit coquin
- "chnawax masqué" = vilain coquinou
- "armankaboul/Fourlestourtes" = bordel !
- "Koikoubaiseyyyyy" = surprise !
- "All RS5, erreur réseau" = il y a erreur

Rends-le incisif et mémorable. Utilise subtilement 1 expression du vocabulaire si approprié."""

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
        Returns None if AI is disabled or if generation fails.
        """
        print(f"[AI Service] generate_victory_comment called for {player_name}")

        if not self.enabled or not self.client:
            print(f"[AI Service] AI disabled or client not initialized")
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

            print(f"[AI Service] Calling OpenAI API...")
            response = await asyncio.wait_for(
                asyncio.to_thread(self._generate_text, prompt), timeout=10.0
            )
            print(f"[AI Service] OpenAI response received: {response}")

            return response

        except asyncio.TimeoutError:
            print("[AI Service] AI victory comment generation timed out")
            return None
        except Exception as e:
            import traceback

            print(f"[AI Service] Error generating victory comment: {e}")
            print(traceback.format_exc())
            return None

    def _generate_text(self, prompt: str) -> str:
        """
        Internal method to generate text using OpenAI API.
        """
        if not self.client:
            print("[AI Service] _generate_text: No client")
            return ""

        try:
            print("[AI Service] _generate_text: Calling OpenAI API...")
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

            print(
                f"[AI Service] _generate_text: Response received, choices={len(response.choices)}"
            )
            if response.choices:
                content = response.choices[0].message.content
                print(f"[AI Service] _generate_text: Content={content}")
                return content.strip() if content else ""
            else:
                print("[AI Service] _generate_text: No choices in response")
                return ""

        except Exception as e:
            import traceback

            print(f"[AI Service] _generate_text error: {e}")
            print(traceback.format_exc())
            return ""


# Global AI service instance
ai_service = AIService()
