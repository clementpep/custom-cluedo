"""
Game manager for handling multiple concurrent games.
Provides in-memory storage and game lifecycle management.
"""

import json
import os
from typing import Dict, Optional, List
from models import Game, Player, CreateGameRequest, GameStatus
from game_engine import GameEngine
from config import settings


class GameManager:
    """Manages multiple game instances in memory."""

    def __init__(self):
        self.games: Dict[str, Game] = {}
        self.load_games()

    def create_game(self, request: CreateGameRequest) -> Game:
        """
        Create a new game instance.
        """
        game_id = Game.generate_game_id()

        # Ensure unique game ID
        while game_id in self.games:
            game_id = Game.generate_game_id()

        game = Game(
            game_id=game_id,
            name=request.game_name,
            narrative_tone=request.narrative_tone,
            custom_prompt=request.custom_prompt,
            rooms=request.rooms,
            custom_weapons=request.custom_weapons,
            custom_suspects=request.custom_suspects,
            use_ai=request.use_ai,
            max_players=settings.MAX_PLAYERS
        )

        self.games[game_id] = game
        self.save_games()

        return game

    def get_game(self, game_id: str) -> Optional[Game]:
        """Retrieve a game by ID."""
        return self.games.get(game_id)

    def join_game(self, game_id: str, player_name: str) -> Optional[Player]:
        """
        Add a player to an existing game.
        Returns the player if successful, None otherwise.
        """
        game = self.get_game(game_id)

        if not game:
            return None

        if game.status != GameStatus.WAITING:
            return None  # Can't join a game in progress

        if game.is_full():
            return None  # Game is full

        player = game.add_player(player_name)
        self.save_games()

        return player

    def start_game(self, game_id: str) -> bool:
        """
        Start a game (initialize cards and solution).
        Returns True if successful.
        """
        game = self.get_game(game_id)

        if not game:
            return False

        if game.status != GameStatus.WAITING:
            return False  # Game already started

        if len(game.players) < settings.MIN_PLAYERS:
            return False  # Not enough players

        # Initialize the game
        GameEngine.initialize_game(game)
        self.save_games()

        return True

    def list_active_games(self) -> List[Dict]:
        """
        List all active games (waiting or in progress).
        Returns simplified game info for listing.
        """
        active_games = []

        for game in self.games.values():
            if game.status in [GameStatus.WAITING, GameStatus.IN_PROGRESS]:
                active_games.append({
                    "game_id": game.game_id,
                    "name": game.name,
                    "status": game.status,
                    "players": len(game.players),
                    "max_players": game.max_players,
                })

        return active_games

    def delete_game(self, game_id: str) -> bool:
        """Delete a game from memory."""
        if game_id in self.games:
            del self.games[game_id]
            self.save_games()
            return True
        return False

    def save_games(self):
        """Persist games to JSON file."""
        try:
            games_data = {
                game_id: game.model_dump()
                for game_id, game in self.games.items()
            }

            with open(settings.GAMES_FILE, 'w') as f:
                json.dump(games_data, f, indent=2)
        except Exception as e:
            print(f"Error saving games: {e}")

    def load_games(self):
        """Load games from JSON file if it exists."""
        if not os.path.exists(settings.GAMES_FILE):
            return

        try:
            with open(settings.GAMES_FILE, 'r') as f:
                games_data = json.load(f)

            for game_id, game_dict in games_data.items():
                self.games[game_id] = Game(**game_dict)
        except Exception as e:
            print(f"Error loading games: {e}")


# Global game manager instance
game_manager = GameManager()
