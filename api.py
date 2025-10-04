"""
FastAPI backend for Cluedo Custom game.
Provides REST API endpoints for game management and actions.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from models import (
    CreateGameRequest,
    JoinGameRequest,
    GameAction,
    Game,
    Player,
    GameStatus
)
from game_manager import game_manager
from game_engine import GameEngine
from ai_service import ai_service
from config import settings


app = FastAPI(title=settings.APP_NAME)

# CORS disabled - not needed when API and Gradio are on same host (localhost)


class GameResponse(BaseModel):
    """Response when creating or joining a game."""
    game_id: str
    player_id: Optional[str] = None
    message: str


class ActionResponse(BaseModel):
    """Response for game actions."""
    success: bool
    message: str
    data: Optional[dict] = None


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "app": settings.APP_NAME,
        "status": "running",
        "ai_enabled": settings.USE_OPENAI
    }


@app.post("/games/create", response_model=GameResponse)
async def create_game(request: CreateGameRequest):
    """
    Create a new game.
    Returns the game ID.
    """
    # Validate room count
    if len(request.rooms) < settings.MIN_ROOMS:
        raise HTTPException(
            status_code=400,
            detail=f"At least {settings.MIN_ROOMS} rooms are required"
        )

    if len(request.rooms) > settings.MAX_ROOMS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {settings.MAX_ROOMS} rooms allowed"
        )

    # Create game
    game = game_manager.create_game(request)

    # Generate AI scenario if enabled
    if game.use_ai and settings.USE_OPENAI:
        from game_engine import DEFAULT_CHARACTERS
        scenario = await ai_service.generate_scenario(
            game.rooms,
            DEFAULT_CHARACTERS
        )
        if scenario:
            game.scenario = scenario
            game_manager.save_games()

    return GameResponse(
        game_id=game.game_id,
        message=f"Game '{game.name}' created successfully"
    )


@app.post("/games/join", response_model=GameResponse)
async def join_game(request: JoinGameRequest):
    """
    Join an existing game.
    Returns the player ID.
    """
    game = game_manager.get_game(request.game_id)

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if game.status != GameStatus.WAITING:
        raise HTTPException(status_code=400, detail="Game has already started")

    if game.is_full():
        raise HTTPException(status_code=400, detail="Game is full")

    player = game_manager.join_game(request.game_id, request.player_name)

    if not player:
        raise HTTPException(status_code=400, detail="Could not join game")

    return GameResponse(
        game_id=game.game_id,
        player_id=player.id,
        message=f"{request.player_name} joined the game"
    )


@app.post("/games/{game_id}/start", response_model=ActionResponse)
async def start_game(game_id: str):
    """
    Start a game (initialize cards and begin play).
    """
    success = game_manager.start_game(game_id)

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Could not start game. Check player count and game status."
        )

    return ActionResponse(
        success=True,
        message="Game started successfully"
    )


@app.get("/games/{game_id}", response_model=Game)
async def get_game(game_id: str):
    """
    Get full game state.
    """
    game = game_manager.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    return game


@app.get("/games/{game_id}/player/{player_id}")
async def get_player_view(game_id: str, player_id: str):
    """
    Get game state from a specific player's perspective.
    Hides other players' cards and the solution.
    """
    game = game_manager.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    player = next((p for p in game.players if p.id == player_id), None)

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Build safe view
    other_players = [
        {
            "name": p.name,
            "is_active": p.is_active,
            "card_count": len(p.cards)
        }
        for p in game.players if p.id != player_id
    ]

    current_player = game.get_current_player()

    return {
        "game_id": game.game_id,
        "game_name": game.name,
        "status": game.status,
        "scenario": game.scenario,
        "rooms": game.rooms,
        "characters": [c.name for c in game.characters],
        "weapons": [w.name for w in game.weapons],
        "my_cards": [c.name for c in player.cards],
        "other_players": other_players,
        "current_turn": current_player.name if current_player else None,
        "is_my_turn": current_player.id == player_id if current_player else False,
        "recent_turns": game.turns[-5:] if game.turns else [],
        "winner": game.winner
    }


@app.post("/games/{game_id}/action", response_model=ActionResponse)
async def perform_action(game_id: str, action: GameAction):
    """
    Perform a game action (suggest, accuse, pass).
    """
    game = game_manager.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Verify it's the player's turn
    if not GameEngine.can_player_act(game, action.player_id):
        raise HTTPException(status_code=403, detail="Not your turn or game not in progress")

    player = next((p for p in game.players if p.id == action.player_id), None)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    result_message = ""
    result_data = {}

    if action.action_type == "pass":
        # Pass turn
        GameEngine.add_turn_record(game, action.player_id, "pass", "Passed turn")
        game.next_turn()
        result_message = f"{player.name} passed their turn"

    elif action.action_type == "suggest":
        # Make a suggestion
        if not all([action.character, action.weapon, action.room]):
            raise HTTPException(status_code=400, detail="Suggestion requires character, weapon, and room")

        can_disprove, disprover, card = GameEngine.check_suggestion(
            game,
            action.player_id,
            action.character,
            action.weapon,
            action.room
        )

        suggestion_text = f"Suggested: {action.character} with {action.weapon} in {action.room}"

        if can_disprove and disprover and card:
            result_message = f"{disprover} disproved the suggestion by showing: {card.name}"
            result_data = {"disproved_by": disprover, "card_shown": card.name}
        else:
            result_message = "No one could disprove the suggestion!"
            result_data = {"disproved_by": None}

        GameEngine.add_turn_record(game, action.player_id, "suggest", suggestion_text)
        game.next_turn()

    elif action.action_type == "accuse":
        # Make an accusation
        if not all([action.character, action.weapon, action.room]):
            raise HTTPException(status_code=400, detail="Accusation requires character, weapon, and room")

        accusation_text = f"Accused: {action.character} with {action.weapon} in {action.room}"

        is_correct, message = GameEngine.process_accusation(
            game,
            action.player_id,
            action.character,
            action.weapon,
            action.room
        )

        GameEngine.add_turn_record(game, action.player_id, "accuse", accusation_text)

        if not is_correct and game.status == GameStatus.IN_PROGRESS:
            game.next_turn()

        result_message = message
        result_data = {"correct": is_correct, "game_finished": game.status == GameStatus.FINISHED}

    else:
        raise HTTPException(status_code=400, detail="Invalid action type")

    game_manager.save_games()

    return ActionResponse(
        success=True,
        message=result_message,
        data=result_data
    )


@app.get("/games/list")
async def list_games():
    """
    List all active games.
    """
    return {"games": game_manager.list_active_games()}


@app.delete("/games/{game_id}")
async def delete_game(game_id: str):
    """
    Delete a game.
    """
    success = game_manager.delete_game(game_id)

    if not success:
        raise HTTPException(status_code=404, detail="Game not found")

    return {"message": "Game deleted successfully"}
