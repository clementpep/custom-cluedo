"""
Main application file for Cluedo Custom.
Integrates FastAPI backend with Gradio frontend interface.
"""

import gradio as gr
import requests
import json
from typing import Optional, List
from config import settings
import uvicorn
import threading
import time


# API base URL (running locally)
API_BASE = "http://localhost:7860"


class GameState:
    """Client-side game state management."""

    def __init__(self):
        self.game_id: Optional[str] = None
        self.player_id: Optional[str] = None
        self.player_name: Optional[str] = None


# Global state
state = GameState()


def create_game(game_name: str, rooms_text: str, use_ai: bool):
    """
    Create a new game.
    """
    if not game_name or not rooms_text:
        return "Please provide a game name and room list", ""

    # Parse rooms (comma or newline separated)
    rooms = [r.strip() for r in rooms_text.replace("\n", ",").split(",") if r.strip()]

    if len(rooms) < settings.MIN_ROOMS:
        return f"Please provide at least {settings.MIN_ROOMS} rooms", ""

    if len(rooms) > settings.MAX_ROOMS:
        return f"Maximum {settings.MAX_ROOMS} rooms allowed", ""

    try:
        response = requests.post(
            f"{API_BASE}/games/create",
            json={"game_name": game_name, "rooms": rooms, "use_ai": use_ai},
            timeout=5,
        )

        if response.status_code == 200:
            data = response.json()
            state.game_id = data["game_id"]
            return (
                f"✓ Game created successfully!\n\nGame ID: {data['game_id']}\n\n"
                f"Share this ID with other players so they can join.",
                data["game_id"],
            )
        else:
            return f"Error: {response.json().get('detail', 'Unknown error')}", ""

    except Exception as e:
        return f"Error creating game: {str(e)}", ""


def join_game(game_id: str, player_name: str):
    """
    Join an existing game.
    """
    if not game_id or not player_name:
        return "Please provide both Game ID and your name"

    try:
        response = requests.post(
            f"{API_BASE}/games/join",
            json={
                "game_id": game_id.strip().upper(),
                "player_name": player_name.strip(),
            },
            timeout=5,
        )

        if response.status_code == 200:
            data = response.json()
            state.game_id = data["game_id"]
            state.player_id = data["player_id"]
            state.player_name = player_name.strip()

            return f"✓ Joined game successfully!\n\nWelcome, {player_name}!"
        else:
            return f"Error: {response.json().get('detail', 'Unknown error')}"

    except Exception as e:
        return f"Error joining game: {str(e)}"


def start_game(game_id: str):
    """
    Start the game.
    """
    if not game_id:
        return "No game selected"

    try:
        response = requests.post(
            f"{API_BASE}/games/{game_id.strip().upper()}/start", timeout=5
        )

        if response.status_code == 200:
            return "✓ Game started! All players can now view their cards and begin playing."
        else:
            return f"Error: {response.json().get('detail', 'Unknown error')}"

    except Exception as e:
        return f"Error starting game: {str(e)}"


def get_player_view():
    """
    Get current game state for the player.
    """
    if not state.game_id or not state.player_id:
        return "Not in a game. Please create or join a game first."

    try:
        response = requests.get(
            f"{API_BASE}/games/{state.game_id}/player/{state.player_id}", timeout=5
        )

        if response.status_code == 200:
            data = response.json()

            # Format output
            output = []
            output.append(f"=== {data['game_name']} ===\n")
            output.append(f"Status: {data['status']}\n")

            if data.get("scenario"):
                output.append(f"\n{data['scenario']}\n")

            output.append(f"\n--- Your Cards ---")
            for card in data["my_cards"]:
                output.append(f"  • {card}")

            output.append(f"\n--- Game Info ---")
            output.append(f"Rooms: {', '.join(data['rooms'])}")
            output.append(f"Characters: {', '.join(data['characters'])}")
            output.append(f"Weapons: {', '.join(data['weapons'])}")

            output.append(f"\n--- Players ---")
            for player in data["other_players"]:
                status = "✓" if player["is_active"] else "✗"
                output.append(
                    f"  {status} {player['name']} ({player['card_count']} cards)"
                )

            if data["current_turn"]:
                turn_marker = "→ YOUR TURN" if data["is_my_turn"] else ""
                output.append(f"\n--- Current Turn ---")
                output.append(f"{data['current_turn']} {turn_marker}")

            if data.get("winner"):
                output.append(f"\n🏆 WINNER: {data['winner']} 🏆")

            if data["recent_turns"]:
                output.append(f"\n--- Recent Actions ---")
                for turn in data["recent_turns"][-3:]:
                    output.append(f"  {turn['player_name']}: {turn['action']}")
                    if turn.get("details"):
                        output.append(f"    {turn['details']}")

            return "\n".join(output)
        else:
            return f"Error: {response.json().get('detail', 'Unknown error')}"

    except Exception as e:
        return f"Error fetching game state: {str(e)}"


def make_suggestion(character: str, weapon: str, room: str):
    """
    Make a suggestion.
    """
    if not state.game_id or not state.player_id:
        return "Not in a game"

    if not all([character, weapon, room]):
        return "Please select character, weapon, and room"

    try:
        response = requests.post(
            f"{API_BASE}/games/{state.game_id}/action",
            json={
                "game_id": state.game_id,
                "player_id": state.player_id,
                "action_type": "suggest",
                "character": character,
                "weapon": weapon,
                "room": room,
            },
            timeout=5,
        )

        if response.status_code == 200:
            data = response.json()
            return f"✓ {data['message']}"
        else:
            return f"Error: {response.json().get('detail', 'Unknown error')}"

    except Exception as e:
        return f"Error: {str(e)}"


def make_accusation(character: str, weapon: str, room: str):
    """
    Make an accusation.
    """
    if not state.game_id or not state.player_id:
        return "Not in a game"

    if not all([character, weapon, room]):
        return "Please select character, weapon, and room"

    try:
        response = requests.post(
            f"{API_BASE}/games/{state.game_id}/action",
            json={
                "game_id": state.game_id,
                "player_id": state.player_id,
                "action_type": "accuse",
                "character": character,
                "weapon": weapon,
                "room": room,
            },
            timeout=5,
        )

        if response.status_code == 200:
            data = response.json()
            return f"✓ {data['message']}"
        else:
            return f"Error: {response.json().get('detail', 'Unknown error')}"

    except Exception as e:
        return f"Error: {str(e)}"


def pass_turn():
    """
    Pass the current turn.
    """
    if not state.game_id or not state.player_id:
        return "Not in a game"

    try:
        response = requests.post(
            f"{API_BASE}/games/{state.game_id}/action",
            json={
                "game_id": state.game_id,
                "player_id": state.player_id,
                "action_type": "pass",
            },
            timeout=5,
        )

        if response.status_code == 200:
            data = response.json()
            return f"✓ {data['message']}"
        else:
            return f"Error: {response.json().get('detail', 'Unknown error')}"

    except Exception as e:
        return f"Error: {str(e)}"


# Sample lists for dropdowns
from game_engine import DEFAULT_CHARACTERS, DEFAULT_WEAPONS


def create_gradio_interface():
    """
    Create the Gradio interface.
    """
    with gr.Blocks(title=settings.APP_NAME, theme=gr.themes.Soft()) as demo:
        gr.Markdown(f"# {settings.APP_NAME}")
        gr.Markdown("A custom Cluedo game for real-world locations")

        with gr.Tab("Create Game"):
            gr.Markdown("### Create a New Game")

            game_name_input = gr.Textbox(
                label="Game Name", placeholder="My Awesome Cluedo Game"
            )

            rooms_input = gr.Textbox(
                label=f"Room Names (comma or newline separated, {settings.MIN_ROOMS}-{settings.MAX_ROOMS} rooms)",
                placeholder="Kitchen, Living Room, Bedroom, Office, Garage, Garden",
                lines=4,
            )

            use_ai_checkbox = gr.Checkbox(
                label="Enable AI narration (requires OpenAI API key)",
                value=False,
                visible=settings.USE_OPENAI,
            )

            create_btn = gr.Button("Create Game", variant="primary", size="lg")
            create_output = gr.Textbox(label="Result", lines=5)
            game_id_display = gr.Textbox(
                label="Game ID (share this)", interactive=False
            )

            create_btn.click(
                create_game,
                inputs=[game_name_input, rooms_input, use_ai_checkbox],
                outputs=[create_output, game_id_display],
            )

        with gr.Tab("Join Game"):
            gr.Markdown("### Join an Existing Game")

            join_game_id = gr.Textbox(label="Game ID", placeholder="ABC123")

            join_player_name = gr.Textbox(
                label="Your Name", placeholder="Detective Smith"
            )

            join_btn = gr.Button("Join Game", variant="primary", size="lg")
            join_output = gr.Textbox(label="Result", lines=3)

            join_btn.click(
                join_game, inputs=[join_game_id, join_player_name], outputs=join_output
            )

            gr.Markdown("---")

            start_game_id = gr.Textbox(label="Game ID to Start", placeholder="ABC123")

            start_btn = gr.Button("Start Game", variant="secondary")
            start_output = gr.Textbox(label="Result", lines=2)

            start_btn.click(start_game, inputs=start_game_id, outputs=start_output)

        with gr.Tab("Play"):
            gr.Markdown("### Game View")

            refresh_btn = gr.Button("🔄 Refresh Game State", size="lg")
            game_view = gr.Textbox(label="Game State", lines=20, max_lines=30)

            refresh_btn.click(get_player_view, outputs=game_view)

            gr.Markdown("### Make a Suggestion")

            with gr.Row():
                suggest_character = gr.Dropdown(
                    label="Character", choices=DEFAULT_CHARACTERS
                )
                suggest_weapon = gr.Dropdown(label="Weapon", choices=DEFAULT_WEAPONS)
                suggest_room = gr.Dropdown(
                    label="Room", choices=[]  # Will be populated from game
                )

            suggest_btn = gr.Button("Make Suggestion", variant="primary")
            suggest_output = gr.Textbox(label="Result", lines=2)

            suggest_btn.click(
                make_suggestion,
                inputs=[suggest_character, suggest_weapon, suggest_room],
                outputs=suggest_output,
            )

            gr.Markdown("### Make an Accusation")
            gr.Markdown("⚠️ Warning: Wrong accusation eliminates you from the game!")

            with gr.Row():
                accuse_character = gr.Dropdown(
                    label="Character", choices=DEFAULT_CHARACTERS
                )
                accuse_weapon = gr.Dropdown(label="Weapon", choices=DEFAULT_WEAPONS)
                accuse_room = gr.Dropdown(label="Room", choices=[])

            accuse_btn = gr.Button("Make Accusation", variant="stop")
            accuse_output = gr.Textbox(label="Result", lines=2)

            accuse_btn.click(
                make_accusation,
                inputs=[accuse_character, accuse_weapon, accuse_room],
                outputs=accuse_output,
            )

            gr.Markdown("---")

            pass_btn = gr.Button("Pass Turn")
            pass_output = gr.Textbox(label="Result", lines=1)

            pass_btn.click(pass_turn, outputs=pass_output)

    return demo


def run_fastapi():
    """
    Run FastAPI server in a separate thread.
    """
    from api import app

    uvicorn.run(app, host=settings.HOST, port=settings.PORT, log_level="info")


if __name__ == "__main__":
    # Start FastAPI in background thread
    api_thread = threading.Thread(target=run_fastapi, daemon=True)
    api_thread.start()

    # Wait for API to start
    time.sleep(2)

    # Launch Gradio interface
    demo = create_gradio_interface()
    demo.launch(
        server_name="127.0.0.1",  # Use localhost instead of 0.0.0.0 for Windows
        server_port=7861,
        share=False,
        show_error=True,
    )
