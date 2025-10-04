"""
Game engine for Cluedo Custom.
Handles game logic, card distribution, turn management, and game rules.
"""

import random
from typing import List, Optional, Tuple
from models import Game, Card, CardType, Solution, GameStatus, Player
from datetime import datetime


# Default character names (can be customized)
DEFAULT_CHARACTERS = [
    "Miss Scarlett",
    "Colonel Mustard",
    "Mrs. White",
    "Reverend Green",
    "Mrs. Peacock",
    "Professor Plum"
]

# Default weapon names (can be customized)
DEFAULT_WEAPONS = [
    "Candlestick",
    "Knife",
    "Lead Pipe",
    "Revolver",
    "Rope",
    "Wrench"
]


class GameEngine:
    """Core game logic engine for Cluedo Custom."""

    @staticmethod
    def initialize_game(game: Game) -> Game:
        """
        Initialize a game with cards and solution.
        Distributes cards among players after setting aside the solution.
        """
        # Create character cards
        game.characters = [
            Card(name=name, card_type=CardType.CHARACTER)
            for name in DEFAULT_CHARACTERS
        ]

        # Create weapon cards
        game.weapons = [
            Card(name=name, card_type=CardType.WEAPON)
            for name in DEFAULT_WEAPONS
        ]

        # Create room cards
        game.room_cards = [
            Card(name=room, card_type=CardType.ROOM)
            for room in game.rooms
        ]

        # Select solution (one of each type)
        solution_character = random.choice(game.characters)
        solution_weapon = random.choice(game.weapons)
        solution_room = random.choice(game.room_cards)

        game.solution = Solution(
            character=solution_character,
            weapon=solution_weapon,
            room=solution_room
        )

        # Remaining cards to distribute
        remaining_cards = []
        remaining_cards.extend([c for c in game.characters if c.name != solution_character.name])
        remaining_cards.extend([w for w in game.weapons if w.name != solution_weapon.name])
        remaining_cards.extend([r for r in game.room_cards if r.name != solution_room.name])

        # Shuffle and distribute
        random.shuffle(remaining_cards)
        GameEngine._distribute_cards(game, remaining_cards)

        # Set game status to in progress
        game.status = GameStatus.IN_PROGRESS
        game.current_player_index = 0

        return game

    @staticmethod
    def _distribute_cards(game: Game, cards: List[Card]):
        """
        Distribute cards evenly among all players.
        """
        num_players = len(game.players)
        if num_players == 0:
            return

        for i, card in enumerate(cards):
            player_index = i % num_players
            game.players[player_index].cards.append(card)

    @staticmethod
    def check_suggestion(
        game: Game,
        player_id: str,
        character: str,
        weapon: str,
        room: str
    ) -> Tuple[bool, Optional[str], Optional[Card]]:
        """
        Process a player's suggestion.
        Returns (can_disprove, disprover_name, card_shown).

        Starting with the next player clockwise, check if anyone can disprove
        the suggestion by showing one matching card.
        """
        player_index = next(
            (i for i, p in enumerate(game.players) if p.id == player_id),
            None
        )
        if player_index is None:
            return False, None, None

        num_players = len(game.players)

        # Check other players clockwise
        for offset in range(1, num_players):
            check_index = (player_index + offset) % num_players
            checker = game.players[check_index]

            # Find matching cards
            matching_cards = [
                card for card in checker.cards
                if card.name in [character, weapon, room]
            ]

            if matching_cards:
                # Show one random matching card
                card_to_show = random.choice(matching_cards)
                return True, checker.name, card_to_show

        # No one can disprove
        return False, None, None

    @staticmethod
    def check_accusation(
        game: Game,
        character: str,
        weapon: str,
        room: str
    ) -> bool:
        """
        Check if an accusation is correct.
        Returns True if the accusation matches the solution.
        """
        if not game.solution:
            return False

        return (
            game.solution.character.name == character and
            game.solution.weapon.name == weapon and
            game.solution.room.name == room
        )

    @staticmethod
    def process_accusation(
        game: Game,
        player_id: str,
        character: str,
        weapon: str,
        room: str
    ) -> Tuple[bool, str]:
        """
        Process a player's accusation.
        Returns (is_correct, message).

        If correct, player wins.
        If incorrect, player is eliminated from the game.
        """
        player = next((p for p in game.players if p.id == player_id), None)
        if not player:
            return False, "Player not found"

        is_correct = GameEngine.check_accusation(game, character, weapon, room)

        if is_correct:
            game.winner = player.name
            game.status = GameStatus.FINISHED
            return True, f"{player.name} wins! The accusation was correct."
        else:
            # Eliminate player
            player.is_active = False

            # Check if only one or no players remain active
            active_players = [p for p in game.players if p.is_active]
            if len(active_players) <= 1:
                game.status = GameStatus.FINISHED
                if active_players:
                    game.winner = active_players[0].name
                    return False, f"{player.name}'s accusation was wrong. {game.winner} wins by elimination!"
                else:
                    return False, "All players eliminated. Game over!"

            return False, f"{player.name}'s accusation was wrong and is eliminated from the game."

    @staticmethod
    def add_turn_record(
        game: Game,
        player_id: str,
        action: str,
        details: Optional[str] = None
    ):
        """Add a turn record to the game history."""
        from models import Turn

        player = next((p for p in game.players if p.id == player_id), None)
        if not player:
            return

        turn = Turn(
            player_id=player_id,
            player_name=player.name,
            action=action,
            details=details,
            timestamp=datetime.now().isoformat()
        )
        game.turns.append(turn)

    @staticmethod
    def get_player_card_names(player: Player) -> List[str]:
        """Get list of card names for a player."""
        return [card.name for card in player.cards]

    @staticmethod
    def can_player_act(game: Game, player_id: str) -> bool:
        """Check if it's the player's turn and they can act."""
        current_player = game.get_current_player()
        if not current_player:
            return False

        return (
            current_player.id == player_id and
            current_player.is_active and
            game.status == GameStatus.IN_PROGRESS
        )
