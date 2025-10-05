"""
Data models for Cluedo Custom game.
Defines the structure of players, cards, and game state.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from enum import Enum
import random
import string


class NarrativeTone(str, Enum):
    """Narrative tone options for the game."""
    SERIOUS = "🕵️ Sérieuse"
    PARODY = "😂 Parodique"
    FANTASY = "🧙‍♂️ Fantastique"
    THRILLER = "🎬 Thriller"
    HORROR = "👻 Horreur"


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
    current_room_index: int = 0  # Position on the board
    has_rolled: bool = False  # Track if player rolled dice this turn


class GameStatus(str, Enum):
    """Status of a game."""
    WAITING = "waiting"  # Waiting for players to join
    IN_PROGRESS = "in_progress"  # Game is running
    FINISHED = "finished"  # Game has ended


class Turn(BaseModel):
    """Represents a turn action in the game."""
    player_id: str
    player_name: str
    action: str  # "move", "suggest", "accuse", "pass"
    details: Optional[str] = None
    ai_comment: Optional[str] = None  # Desland's sarcastic comment
    timestamp: str


class Solution(BaseModel):
    """The secret solution to the mystery."""
    character: Card
    weapon: Card
    room: Card


class InvestigationNote(BaseModel):
    """Player's notes on the investigation."""
    player_id: str
    element_name: str  # Name of suspect/weapon/room
    element_type: str  # "suspect", "weapon", "room"
    status: str  # "unknown", "eliminated", "maybe"


class RoomPosition(BaseModel):
    """Position of a room on the board."""
    name: str
    x: int  # Grid X position
    y: int  # Grid Y position


class BoardLayout(BaseModel):
    """Board layout configuration."""
    rooms: List[RoomPosition] = Field(default_factory=list)
    grid_width: int = 8
    grid_height: int = 8


class Game(BaseModel):
    """Represents a complete game instance."""
    game_id: str
    name: str
    status: GameStatus = GameStatus.WAITING

    # Theme and narrative
    narrative_tone: str = NarrativeTone.SERIOUS.value
    custom_prompt: Optional[str] = None

    # Game elements (customizable)
    rooms: List[str]
    custom_weapons: List[str] = Field(default_factory=list)
    custom_suspects: List[str] = Field(default_factory=list)

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

    # Investigation notes (for UI)
    investigation_notes: List[InvestigationNote] = Field(default_factory=list)

    # Board layout
    board_layout: Optional[BoardLayout] = None

    # AI-generated content
    scenario: Optional[str] = None

    @staticmethod
    def generate_game_id() -> str:
        """Generate a unique 4-character game ID (like AB7F)."""
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=4))

    def add_player(self, player_name: str) -> Player:
        """Add a new player to the game."""
        player_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        # All players start in the first room
        player = Player(id=player_id, name=player_name, current_room_index=0)
        self.players.append(player)
        return player

    def get_current_player(self) -> Optional[Player]:
        """Get the player whose turn it is."""
        if not self.players:
            return None
        return self.players[self.current_player_index]

    def next_turn(self):
        """Move to the next active player's turn."""
        if not self.players:
            return

        # Reset has_rolled for current player
        if self.current_player_index < len(self.players):
            self.players[self.current_player_index].has_rolled = False

        # Skip eliminated players
        attempts = 0
        while attempts < len(self.players):
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            if self.players[self.current_player_index].is_active:
                break
            attempts += 1

    def is_full(self) -> bool:
        """Check if the game has reached maximum players."""
        return len(self.players) >= self.max_players


class CreateGameRequest(BaseModel):
    """Request to create a new game."""
    game_name: str
    narrative_tone: str = NarrativeTone.SERIOUS.value
    custom_prompt: Optional[str] = None
    rooms: List[str]
    custom_weapons: List[str]
    custom_suspects: List[str]
    use_ai: bool = False
    board_layout: Optional[BoardLayout] = None


class JoinGameRequest(BaseModel):
    """Request to join an existing game."""
    game_id: str
    player_name: str


class GameAction(BaseModel):
    """Request to perform a game action."""
    game_id: str
    player_id: str
    action_type: str  # "move", "suggest", "accuse", "pass"
    # For movement
    dice_roll: Optional[int] = None
    target_room_index: Optional[int] = None
    # For suggestions/accusations
    character: Optional[str] = None
    weapon: Optional[str] = None
    room: Optional[str] = None
