"""
Data models for Cluedo Custom game.
Defines the structure of players, cards, and game state.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from enum import Enum
import random
import string


class CardType(str, Enum):
    """Types of cards in the game."""
    CHARACTER = "character"
    WEAPON = "weapon"
    ROOM = "room"


class Card(BaseModel):
    """Represents a single card in the game."""
    name: str
    card_type: CardType


class Player(BaseModel):
    """Represents a player in the game."""
    id: str
    name: str
    cards: List[Card] = Field(default_factory=list)
    is_active: bool = True


class GameStatus(str, Enum):
    """Status of a game."""
    WAITING = "waiting"  # Waiting for players to join
    IN_PROGRESS = "in_progress"  # Game is running
    FINISHED = "finished"  # Game has ended


class Turn(BaseModel):
    """Represents a turn action in the game."""
    player_id: str
    player_name: str
    action: str  # "move", "suggest", "accuse"
    details: Optional[str] = None
    timestamp: str


class Solution(BaseModel):
    """The secret solution to the mystery."""
    character: Card
    weapon: Card
    room: Card


class Game(BaseModel):
    """Represents a complete game instance."""
    game_id: str
    name: str
    status: GameStatus = GameStatus.WAITING
    rooms: List[str]
    use_ai: bool = False

    # Players
    players: List[Player] = Field(default_factory=list)
    max_players: int = 8
    current_player_index: int = 0

    # Cards
    characters: List[Card] = Field(default_factory=list)
    weapons: List[Card] = Field(default_factory=list)
    room_cards: List[Card] = Field(default_factory=list)

    # Solution
    solution: Optional[Solution] = None

    # Game state
    turns: List[Turn] = Field(default_factory=list)
    winner: Optional[str] = None

    # AI-generated content
    scenario: Optional[str] = None

    @staticmethod
    def generate_game_id() -> str:
        """Generate a unique 6-character game ID."""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    def add_player(self, player_name: str) -> Player:
        """Add a new player to the game."""
        player_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        player = Player(id=player_id, name=player_name)
        self.players.append(player)
        return player

    def get_current_player(self) -> Optional[Player]:
        """Get the player whose turn it is."""
        if not self.players:
            return None
        return self.players[self.current_player_index]

    def next_turn(self):
        """Move to the next player's turn."""
        if self.players:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)

    def is_full(self) -> bool:
        """Check if the game has reached maximum players."""
        return len(self.players) >= self.max_players


class CreateGameRequest(BaseModel):
    """Request to create a new game."""
    game_name: str
    rooms: List[str]
    use_ai: bool = False


class JoinGameRequest(BaseModel):
    """Request to join an existing game."""
    game_id: str
    player_name: str


class GameAction(BaseModel):
    """Request to perform a game action."""
    game_id: str
    player_id: str
    action_type: str  # "suggest", "accuse", "pass"
    character: Optional[str] = None
    weapon: Optional[str] = None
    room: Optional[str] = None
