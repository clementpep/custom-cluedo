"""
FastAPI backend for Cluedo Custom
Serves both API and React frontend
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os

from backend.models import CreateGameRequest, GameStatus
from backend.game_manager import game_manager
from backend.game_engine import GameEngine
from backend.defaults import get_default_game_config, DEFAULT_THEMES

app = FastAPI(title="Cluedo Custom API")

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== API ROUTES ====================

@app.get("/api/health")
async def health():
    return {"status": "ok", "message": "Cluedo Custom API is running"}


@app.get("/api/themes")
async def get_themes():
    """Get available game themes"""
    return {"themes": DEFAULT_THEMES}


class QuickCreateRequest(BaseModel):
    theme: str = "classic"
    player_name: str


@app.post("/api/games/quick-create")
async def quick_create_game(req: QuickCreateRequest):
    """Create a game quickly with default theme"""
    try:
        config = get_default_game_config(req.theme)

        game_req = CreateGameRequest(
            game_name=config["name"],
            narrative_tone=config["tone"],
            custom_prompt=None,
            rooms=config["rooms"],
            custom_weapons=config["weapons"],
            custom_suspects=config["suspects"],
            use_ai=False
        )

        game = game_manager.create_game(game_req)

        # Auto-join creator as first player
        player = game_manager.join_game(game.game_id, req.player_name)

        return {
            "game_id": game.game_id,
            "player_id": player.id if player else None,
            "game_name": game.name,
            "theme": req.theme
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class JoinRequest(BaseModel):
    game_id: str
    player_name: str


@app.post("/api/games/join")
async def join_game(req: JoinRequest):
    """Join an existing game"""
    game = game_manager.get_game(req.game_id.upper())

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if game.status != GameStatus.WAITING:
        raise HTTPException(status_code=400, detail="Game already started")

    if game.is_full():
        raise HTTPException(status_code=400, detail="Game is full")

    player = game_manager.join_game(req.game_id.upper(), req.player_name)

    if not player:
        raise HTTPException(status_code=400, detail="Could not join game")

    return {
        "game_id": game.game_id,
        "player_id": player.id,
        "player_name": player.name
    }


@app.post("/api/games/{game_id}/start")
async def start_game(game_id: str):
    """Start a game"""
    success = game_manager.start_game(game_id.upper())

    if not success:
        raise HTTPException(status_code=400, detail="Cannot start game (need min 3 players)")

    game = game_manager.get_game(game_id.upper())
    return {
        "status": "started",
        "first_player": game.get_current_player().name if game else None
    }


@app.get("/api/games/{game_id}/state/{player_id}")
async def get_game_state(game_id: str, player_id: str):
    """Get game state for a specific player"""
    game = game_manager.get_game(game_id.upper())

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    player = next((p for p in game.players if p.id == player_id), None)

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    current_player = game.get_current_player()

    # Build player-specific view
    return {
        "game_id": game.game_id,
        "game_name": game.name,
        "status": game.status.value,
        "scenario": game.scenario,
        "rooms": game.rooms,
        "suspects": [c.name for c in game.characters],
        "weapons": [w.name for w in game.weapons],
        "my_cards": [{"name": c.name, "type": c.card_type.value} for c in player.cards],
        "my_position": player.current_room_index,
        "current_room": game.rooms[player.current_room_index] if game.rooms else None,
        "players": [
            {
                "name": p.name,
                "is_active": p.is_active,
                "position": p.current_room_index,
                "room": game.rooms[p.current_room_index] if game.rooms else None,
                "is_me": p.id == player_id
            }
            for p in game.players
        ],
        "current_turn": {
            "player_name": current_player.name if current_player else None,
            "is_my_turn": current_player.id == player_id if current_player else False
        },
        "recent_actions": [
            {
                "player": t.player_name,
                "action": t.action,
                "details": t.details,
                "ai_comment": t.ai_comment
            }
            for t in game.turns[-5:]
        ],
        "winner": game.winner
    }


class DiceRollRequest(BaseModel):
    player_id: str


@app.post("/api/games/{game_id}/roll")
async def roll_dice(game_id: str, req: DiceRollRequest):
    """Roll dice and move player"""
    game = game_manager.get_game(game_id.upper())

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if not GameEngine.can_player_act(game, req.player_id):
        raise HTTPException(status_code=400, detail="Not your turn")

    # Roll dice
    dice = GameEngine.roll_dice()

    # Move player
    success, msg, new_pos = GameEngine.move_player(game, req.player_id, dice)

    if not success:
        raise HTTPException(status_code=400, detail=msg)

    # Record turn
    GameEngine.add_turn_record(game, req.player_id, "move", msg)
    game_manager.save_games()

    return {
        "dice_value": dice,
        "new_position": new_pos,
        "new_room": game.rooms[new_pos],
        "message": msg
    }


class SuggestionRequest(BaseModel):
    player_id: str
    suspect: str
    weapon: str
    room: str


@app.post("/api/games/{game_id}/suggest")
async def make_suggestion(game_id: str, req: SuggestionRequest):
    """Make a suggestion"""
    game = game_manager.get_game(game_id.upper())

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if not GameEngine.can_player_act(game, req.player_id):
        raise HTTPException(status_code=400, detail="Not your turn")

    # Check if player is in the room
    can_suggest, error = GameEngine.can_make_suggestion(game, req.player_id, req.room)
    if not can_suggest:
        raise HTTPException(status_code=400, detail=error)

    # Process suggestion
    can_disprove, disprover, card = GameEngine.check_suggestion(
        game, req.player_id, req.suspect, req.weapon, req.room
    )

    result = {
        "suggestion": f"{req.suspect} + {req.weapon} + {req.room}",
        "was_disproven": can_disprove,
        "disprover": disprover if can_disprove else None,
        "card_shown": card.name if card else None
    }

    # Record turn
    GameEngine.add_turn_record(
        game,
        req.player_id,
        "suggest",
        result["suggestion"]
    )

    game.next_turn()
    game_manager.save_games()

    return result


class AccusationRequest(BaseModel):
    player_id: str
    suspect: str
    weapon: str
    room: str


@app.post("/api/games/{game_id}/accuse")
async def make_accusation(game_id: str, req: AccusationRequest):
    """Make an accusation"""
    game = game_manager.get_game(game_id.upper())

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if not GameEngine.can_player_act(game, req.player_id):
        raise HTTPException(status_code=400, detail="Not your turn")

    # Process accusation
    is_correct, message = GameEngine.process_accusation(
        game, req.player_id, req.suspect, req.weapon, req.room
    )

    # Record turn
    GameEngine.add_turn_record(
        game,
        req.player_id,
        "accuse",
        f"{req.suspect} + {req.weapon} + {req.room}"
    )

    if not is_correct and game.status == GameStatus.IN_PROGRESS:
        game.next_turn()

    game_manager.save_games()

    return {
        "is_correct": is_correct,
        "message": message,
        "winner": game.winner
    }


class PassRequest(BaseModel):
    player_id: str


@app.post("/api/games/{game_id}/pass")
async def pass_turn(game_id: str, req: PassRequest):
    """Pass the turn"""
    game = game_manager.get_game(game_id.upper())

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if not GameEngine.can_player_act(game, req.player_id):
        raise HTTPException(status_code=400, detail="Not your turn")

    # Record turn
    GameEngine.add_turn_record(game, req.player_id, "pass", "Passed turn")

    game.next_turn()
    game_manager.save_games()

    next_player = game.get_current_player()

    return {
        "message": "Turn passed",
        "next_player": next_player.name if next_player else None
    }


# ==================== SERVE REACT APP ====================

# Check if frontend build exists
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.exists(frontend_path):
    # Serve static files
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_react(full_path: str):
        """Serve React app for all non-API routes"""
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found")

        index_file = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        else:
            raise HTTPException(status_code=404, detail="Frontend not built")
else:
    @app.get("/")
    async def root():
        return {
            "message": "Cluedo Custom API",
            "docs": "/docs",
            "frontend": "Not built yet. Run: cd frontend && npm run build"
        }
