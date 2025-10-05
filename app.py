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


# Determine runtime environment
import os

IS_HUGGINGFACE = os.getenv("SPACE_ID") is not None

# API base URL (only used in local mode)
API_BASE = "http://localhost:8000"


class GameState:
    """Client-side game state management."""

    def __init__(self):
        self.game_id: Optional[str] = None
        self.player_id: Optional[str] = None
        self.player_name: Optional[str] = None


# Global state
state = GameState()


def create_game(
    game_name: str,
    narrative_tone: str,
    custom_prompt: str,
    rooms_text: str,
    weapons_text: str,
    suspects_text: str,
    use_ai: bool
):
    """
    Create a new game with custom elements.
    """
    if not game_name or not rooms_text:
        return "❌ Fournissez un titre d'enquête et une liste de lieux", ""

    # Parse inputs (comma or newline separated)
    rooms = [r.strip() for r in rooms_text.replace("\n", ",").split(",") if r.strip()]
    weapons = [w.strip() for w in weapons_text.replace("\n", ",").split(",") if w.strip()]
    suspects = [s.strip() for s in suspects_text.replace("\n", ",").split(",") if s.strip()]

    # Validation
    if len(rooms) < settings.MIN_ROOMS:
        return f"❌ Il faut au moins {settings.MIN_ROOMS} lieux", ""

    if len(rooms) > settings.MAX_ROOMS:
        return f"❌ Maximum {settings.MAX_ROOMS} lieux autorisés", ""

    if len(weapons) < 3:
        return "❌ Il faut au moins 3 armes", ""

    if len(suspects) < 3:
        return "❌ Il faut au moins 3 suspects", ""

    try:
        if IS_HUGGINGFACE:
            from game_manager import game_manager
            from models import CreateGameRequest

            request = CreateGameRequest(
                game_name=game_name,
                narrative_tone=narrative_tone,
                custom_prompt=custom_prompt if custom_prompt else None,
                rooms=rooms,
                custom_weapons=weapons,
                custom_suspects=suspects,
                use_ai=use_ai
            )
            game = game_manager.create_game(request)

            # Generate AI scenario if enabled
            if game.use_ai and settings.USE_OPENAI:
                from ai_service import ai_service
                import asyncio

                try:
                    scenario = asyncio.run(
                        ai_service.generate_scenario(
                            game.rooms,
                            game.custom_suspects,
                            game.narrative_tone
                        )
                    )
                    if scenario:
                        game.scenario = scenario
                        game_manager.save_games()
                except:
                    pass  # AI is optional

            state.game_id = game.game_id
            return (
                f"✅ Enquête créée !\n\n"
                f"🔑 Code d'Enquête : **{game.game_id}**\n\n"
                f"📤 Partagez ce code avec les autres joueurs\n"
                f"ℹ️ Minimum {settings.MIN_PLAYERS} joueurs requis pour démarrer",
                game.game_id,
            )
        else:
            # HTTP API call (local mode)
            response = requests.post(
                f"{API_BASE}/games/create",
                json={
                    "game_name": game_name,
                    "narrative_tone": narrative_tone,
                    "custom_prompt": custom_prompt if custom_prompt else None,
                    "rooms": rooms,
                    "custom_weapons": weapons,
                    "custom_suspects": suspects,
                    "use_ai": use_ai
                },
                timeout=5,
            )

            if response.status_code == 200:
                data = response.json()
                state.game_id = data["game_id"]
                return (
                    f"✅ Enquête créée !\n\n"
                    f"🔑 Code : **{data['game_id']}**\n\n"
                    f"📤 Partagez ce code\n"
                    f"ℹ️ Min. {settings.MIN_PLAYERS} joueurs",
                    data["game_id"],
                )
            else:
                return f"❌ Erreur : {response.json().get('detail', 'Erreur inconnue')}", ""

    except Exception as e:
        return f"❌ Erreur : {str(e)}", ""


def join_game(game_id: str, player_name: str):
    """
    Join an existing game.
    """
    if not game_id or not player_name:
        return "❌ Fournissez le code d'enquête et votre nom !"

    try:
        game_id = game_id.strip().upper()
        player_name = player_name.strip()

        if IS_HUGGINGFACE:
            # Direct backend call
            from game_manager import game_manager
            from models import GameStatus

            game = game_manager.get_game(game_id)
            if not game:
                return "❌ Enquête introuvable !"

            if game.status != GameStatus.WAITING:
                return "❌ La partie a déjà commencé !"

            if game.is_full():
                return "❌ Partie complète (maximum 8 joueurs) !"

            player = game_manager.join_game(game_id, player_name)
            if not player:
                return "❌ Impossible de rejoindre l'enquête !"

            state.game_id = game_id
            state.player_id = player.id
            state.player_name = player_name

            return (
                f"✅ Enquête rejointe !\n\n"
                f"👋 Bienvenue, {player_name} !\n\n"
                f"⏳ Attendez que le créateur démarre la partie\n"
                f"📖 Consultez l'onglet 🔎 Enquêter pour voir l'état"
            )
        else:
            # HTTP API call (local mode)
            response = requests.post(
                f"{API_BASE}/games/join",
                json={
                    "game_id": game_id,
                    "player_name": player_name,
                },
                timeout=5,
            )

            if response.status_code == 200:
                data = response.json()
                state.game_id = data["game_id"]
                state.player_id = data["player_id"]
                state.player_name = player_name

                return (
                    f"✅ Enquête rejointe avec succès !\n\n"
                    f"👋 Bienvenue, {player_name} !\n\n"
                    f"⏳ Attendez que le chnawax originel (le créateur) démarre la partie...\n"
                    f"📖 Allez dans l'onglet 🔎 Enquêter pour voir l'état de la partie."
                )
            else:
                return f"❌ All RS5, erreur réseau (fourlestourtes et les bourbillats) : {response.json().get('detail', 'Erreur inconnue')}"

    except Exception as e:
        return f"❌ Koikoubaiseyyyyy ! Erreur : {str(e)}"


def start_game(game_id: str):
    """
    Start the game.
    """
    if not game_id:
        return "❌ Triple monstre coucouuuuu ! Aucune enuête sélectionnée !"

    try:
        game_id = game_id.strip().upper()

        if IS_HUGGINGFACE:
            # Direct backend call
            from game_manager import game_manager

            success = game_manager.start_game(game_id)

            if not success:
                return f"❌ Impossible de démarrer ! Minimum {settings.MIN_PLAYERS} joueurs requis."

            game = game_manager.get_game(game_id)

            return (
                f"🎬 L'ENQUÊTE COMMENCE !\n\n"
                f"🃏 Les cartes ont été distribuées\n"
                f"🎲 Tous les joueurs démarrent dans : {game.rooms[0] if game.rooms else '(aucun lieu)'}\n"
                f"🔍 À vous de découvrir qui a commis le crime, avec quelle arme et dans quel lieu !\n\n"
                f"➡️ Allez dans l'onglet 🔎 Enquêter pour commencer à jouer"
            )
        else:
            # HTTP API call (local mode)
            response = requests.post(f"{API_BASE}/games/{game_id}/start", timeout=5)

            if response.status_code == 200:
                return (
                    f"🎬 L'ENQUÊTE COMMENCE !\n\n"
                    f"🃏 Les cartes ont été distribuées\n"
                    f"🔍 À vous de découvrir qui a commis le crime !\n\n"
                    f"➡️ Allez dans l'onglet 🔎 Enquêter pour commencer"
                )
            else:
                return f"❌ Erreur : {response.json().get('detail', 'Erreur inconnue')}"

    except Exception as e:
        return f"❌ Yamete coudasai ! Erreur au démarrage : {str(e)}"


def get_player_view():
    """
    Get current game state for the player.
    """
    if not state.game_id or not state.player_id:
        return (
            "❌ Eskilibass ! Vous n'êtes pas dans une enquête.\n\n"
            "➡️ Créer une nouvelle enquête ou rejoignez d'autres péchailloux masqués."
        )

    try:
        if IS_HUGGINGFACE:
            # Direct backend call
            from game_manager import game_manager

            game = game_manager.get_game(state.game_id)

            if not game:
                return "❌ All RS5, erreur réseau ! Enquête introuvable... Fourlestourtes et les bourbillats !"

            player = next((p for p in game.players if p.id == state.player_id), None)

            if not player:
                return "❌ Poupée en pénitence calisse ! Péchailloux masqué..."

            # Build safe view
            all_players = [
                {
                    "name": p.name,
                    "is_active": p.is_active,
                    "card_count": len(p.cards),
                    "position": p.current_room_index
                }
                for p in game.players
            ]

            current_player = game.get_current_player()

            data = {
                "game_id": game.game_id,
                "game_name": game.name,
                "status": game.status,
                "scenario": game.scenario,
                "rooms": game.rooms,
                "characters": [c.name for c in game.characters],
                "weapons": [w.name for w in game.weapons],
                "my_cards": [c.name for c in player.cards],
                "my_position": player.current_room_index,
                "all_players": all_players,
                "current_turn": current_player.name if current_player else None,
                "is_my_turn": (
                    current_player.id == state.player_id if current_player else False
                ),
                "recent_turns": game.turns[-5:] if game.turns else [],
                "winner": game.winner,
            }
        else:
            # HTTP API call (local mode)
            response = requests.get(
                f"{API_BASE}/games/{state.game_id}/player/{state.player_id}", timeout=5
            )

            if response.status_code == 200:
                data = response.json()
            else:
                return f"❌ Erreur : {response.json().get('detail', 'Erreur inconnue')}"

        # Format output (common for both modes)
        output = []
        output.append(f"═══ 🎮 {data['game_name']} ═══\n")

        status_map = {
            "waiting": "⏳ En attente de joueurs...",
            "in_progress": "🎲 Partie en cours",
            "finished": "🏆 Partie terminée",
        }
        output.append(f"📊 Statut : {status_map.get(data['status'], data['status'])}\n")

        if data.get("scenario"):
            output.append(f"\n📜 Scénario :\n{data['scenario']}\n")

        # Show player's current position if game started
        if data.get("my_position") is not None and data["rooms"]:
            current_room = data["rooms"][data["my_position"]]
            output.append(f"\n📍 VOTRE POSITION : **{current_room}**")

        output.append(f"\n━━━ 🃏 VOS CARTES ━━━")
        output.append("(Ces éléments NE SONT PAS la solution)")
        for card in data["my_cards"]:
            output.append(f"  🔸 {card}")

        output.append(f"\n━━━ 🏠 PLATEAU DE JEU (Circuit) ━━━")
        # Show rooms with player positions in circuit order
        rooms_display = []
        for idx, room in enumerate(data["rooms"]):
            players_here = [p["name"] for p in data.get("all_players", []) if p.get("position") == idx]

            # Visual indicator
            if players_here:
                icon = "👥"
                player_names = ', '.join(players_here)
                rooms_display.append(f"  {idx+1}. {icon} **{room}** → {player_names}")
            else:
                icon = "🚪"
                rooms_display.append(f"  {idx+1}. {icon} {room}")

        output.extend(rooms_display)
        output.append(f"  └─→ Circuit fermé (retour à {data['rooms'][0]})")

        output.append(f"\n━━━ ℹ️ ÉLÉMENTS DU JEU ━━━")
        output.append(f"👤 Suspects : {', '.join(data['characters'])}")
        output.append(f"🔪 Armes : {', '.join(data['weapons'])}")

        output.append(f"\n━━━ 👥 JOUEURS ━━━")
        for player in data.get("all_players", []):
            status_icon = "✅" if player["is_active"] else "❌"
            position = data["rooms"][player["position"]] if player.get("position") is not None else "?"
            output.append(
                f"  {status_icon} {player['name']} - {position} ({player['card_count']} cartes)"
            )

        if data["current_turn"]:
            turn_marker = (
                "👉 C'EST VOTRE TOUR !" if data["is_my_turn"] else ""
            )
            output.append(f"\n━━━ 🎯 TOUR ACTUEL ━━━")
            output.append(f"🎲 {data['current_turn']} {turn_marker}")

        if data.get("winner"):
            output.append(
                f"\n\n🏆🏆🏆 VAINQUEUR : {data['winner']} 🏆🏆🏆"
            )

        if data["recent_turns"]:
            output.append(f"\n━━━ 📰 HISTORIQUE (5 dernières actions) ━━━")
            for turn in data["recent_turns"][-5:]:
                output.append(f"  • {turn['player_name']}: {turn['action']}")
                if turn.get("details"):
                    output.append(f"    ↪ {turn['details']}")
                if turn.get("ai_comment"):
                    output.append(f"    🗣️ Desland: {turn['ai_comment']}")

        return "\n".join(output)

    except Exception as e:
        return f"❌ Erreur réseau (fourlestourtes et les bourbillats) : {str(e)}"


def make_suggestion(character: str, weapon: str, room: str):
    """
    Make a suggestion.
    """
    if not state.game_id or not state.player_id:
        return "❌ Vous n'êtes pas dans une enquête"

    if not all([character, weapon, room]):
        return "❌ Choisissez un suspect, une arme et un lieu"

    try:
        if IS_HUGGINGFACE:
            from game_manager import game_manager
            from game_engine import GameEngine
            from ai_service import ai_service
            import asyncio

            game = game_manager.get_game(state.game_id)
            if not game:
                return "❌ Enquête introuvable"

            if not GameEngine.can_player_act(game, state.player_id):
                return "❌ Ce n'est pas votre tour !"

            # Check if player is in the correct room
            can_suggest, error_msg = GameEngine.can_make_suggestion(game, state.player_id, room)
            if not can_suggest:
                return f"❌ {error_msg}"

            player = next((p for p in game.players if p.id == state.player_id), None)
            if not player:
                return "❌ Joueur introuvable"

            # Process suggestion
            can_disprove, disprover, card = GameEngine.check_suggestion(
                game, state.player_id, character, weapon, room
            )

            suggestion_text = f"{character} avec {weapon} dans {room}"

            # Generate AI comment if enabled
            ai_comment = None
            if game.use_ai and settings.USE_OPENAI:
                try:
                    ai_comment = asyncio.run(
                        ai_service.generate_suggestion_comment(
                            player.name,
                            character,
                            weapon,
                            room,
                            can_disprove,
                            game.narrative_tone
                        )
                    )
                except:
                    pass

            # Build response message
            if can_disprove and disprover and card:
                message = f"💭 {disprover} réfute en montrant : **{card.name}**"
            else:
                message = "💭 Personne ne peut réfuter cette suggestion !"

            # Add AI comment if available
            if ai_comment:
                message += f"\n\n🗣️ **Desland** : {ai_comment}"

            GameEngine.add_turn_record(
                game, state.player_id, "suggest", suggestion_text, ai_comment
            )
            game.next_turn()
            game_manager.save_games()

            message += "\n\n➡️ Notez cette information dans votre feuille d'enquête !"
            return message

        else:
            # HTTP API call (local mode)
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
                return data.get("message", "Suggestion effectuée")
            else:
                return f"❌ Erreur : {response.json().get('detail', 'Erreur inconnue')}"

    except Exception as e:
        return f"❌ Erreur : {str(e)}"


def make_accusation(character: str, weapon: str, room: str):
    """
    Make an accusation.
    """
    if not state.game_id or not state.player_id:
        return "❌ Vous n'êtes pas dans une enquête"

    if not all([character, weapon, room]):
        return "❌ Choisissez un suspect, une arme et un lieu"

    try:
        if IS_HUGGINGFACE:
            from game_manager import game_manager
            from game_engine import GameEngine
            from models import GameStatus
            from ai_service import ai_service
            import asyncio

            game = game_manager.get_game(state.game_id)
            if not game:
                return "❌ Enquête introuvable"

            if not GameEngine.can_player_act(game, state.player_id):
                return "❌ Ce n'est pas votre tour !"

            player = next((p for p in game.players if p.id == state.player_id), None)
            if not player:
                return "❌ Joueur introuvable"

            accusation_text = f"{character} avec {weapon} dans {room}"

            is_correct, message = GameEngine.process_accusation(
                game, state.player_id, character, weapon, room
            )

            # Generate AI comment if enabled
            ai_comment = None
            if game.use_ai and settings.USE_OPENAI:
                try:
                    ai_comment = asyncio.run(
                        ai_service.generate_accusation_comment(
                            player.name,
                            character,
                            weapon,
                            room,
                            is_correct,
                            game.narrative_tone
                        )
                    )
                except:
                    pass

            GameEngine.add_turn_record(game, state.player_id, "accuse", accusation_text, ai_comment)

            if not is_correct and game.status == GameStatus.IN_PROGRESS:
                game.next_turn()

            game_manager.save_games()

            # Build response
            if is_correct:
                response = f"🎉🏆 {message} 🎉🏆\n\nVous avez résolu le mystère !"
            else:
                response = f"💀 {message}\n\nVous avez été éliminé !\nVous pouvez toujours aider en réfutant les théories des autres."

            if ai_comment:
                response += f"\n\n🗣️ **Desland** : {ai_comment}"

            return response

        else:
            # HTTP API call (local mode)
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
                return data.get("message", "Accusation effectuée")
            else:
                return f"❌ Erreur : {response.json().get('detail', 'Erreur inconnue')}"

    except Exception as e:
        return f"❌ Erreur : {str(e)}"


def roll_and_move():
    """
    Roll dice and move the player.
    """
    if not state.game_id or not state.player_id:
        return "❌ Vous n'êtes pas dans une enquête"

    try:
        if IS_HUGGINGFACE:
            from game_manager import game_manager
            from game_engine import GameEngine

            game = game_manager.get_game(state.game_id)
            if not game:
                return "❌ Enquête introuvable"

            if not GameEngine.can_player_act(game, state.player_id):
                return "❌ Ce n'est pas votre tour !"

            # Roll dice
            dice_roll = GameEngine.roll_dice()

            # Move player
            success, message, new_room_index = GameEngine.move_player(
                game, state.player_id, dice_roll
            )

            if not success:
                return f"❌ {message}"

            # Record turn
            GameEngine.add_turn_record(game, state.player_id, "move", message)
            game_manager.save_games()

            current_room = game.rooms[new_room_index]
            return f"🎲 {message}\n\n📍 Vous êtes maintenant dans : **{current_room}**\n\nVous pouvez faire une suggestion dans cette pièce ou passer votre tour."

        else:
            # HTTP API (local mode)
            response = requests.post(
                f"{API_BASE}/games/{state.game_id}/action",
                json={
                    "game_id": state.game_id,
                    "player_id": state.player_id,
                    "action_type": "move"
                },
                timeout=5,
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("message", "Déplacé avec succès")
            else:
                return f"❌ Erreur : {response.json().get('detail', 'Erreur inconnue')}"

    except Exception as e:
        return f"❌ Erreur : {str(e)}"


def pass_turn():
    """
    Pass the current turn.
    """
    if not state.game_id or not state.player_id:
        return "❌ Vous n'êtes pas dans une enquête"

    try:
        if IS_HUGGINGFACE:
            from game_manager import game_manager
            from game_engine import GameEngine

            game = game_manager.get_game(state.game_id)
            if not game:
                return "❌ Enquête introuvable"

            if not GameEngine.can_player_act(game, state.player_id):
                return "❌ Ce n'est pas votre tour !"

            # Pass turn
            GameEngine.add_turn_record(game, state.player_id, "pass", "Tour passé")
            game.next_turn()
            game_manager.save_games()

            next_player = game.get_current_player()
            return f"✅ Tour passé !\n\n➡️ C'est maintenant au tour de {next_player.name if next_player else 'quelqu\'un'}."

        else:
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
                return "✅ Tour passé !"
            else:
                return f"❌ Erreur : {response.json().get('detail', 'Erreur inconnue')}"

    except Exception as e:
        return f"❌ Erreur : {str(e)}"


# Sample lists for dropdowns
from game_engine import DEFAULT_CHARACTERS, DEFAULT_WEAPONS


def create_gradio_interface():
    """
    Create the Gradio interface.
    """
    # Custom dark detective/horror theme
    custom_theme = gr.themes.Base(
        primary_hue="red",
        secondary_hue="slate",
        neutral_hue="stone",
        font=("ui-serif", "Georgia", "serif"),
    ).set(
        body_background_fill="*neutral_950",
        body_background_fill_dark="*neutral_950",
        body_text_color="*neutral_200",
        body_text_color_dark="*neutral_200",
        button_primary_background_fill="*primary_700",
        button_primary_background_fill_dark="*primary_800",
        button_primary_text_color="white",
        button_secondary_background_fill="*neutral_700",
        button_secondary_background_fill_dark="*neutral_800",
        input_background_fill="*neutral_800",
        input_background_fill_dark="*neutral_900",
        input_border_color="*neutral_700",
        block_background_fill="*neutral_900",
        block_background_fill_dark="*neutral_900",
        block_border_color="*neutral_700",
        block_label_text_color="*primary_400",
        block_title_text_color="*primary_300",
    )

    custom_css = """
    @import url('https://fonts.googleapis.com/css2?family=Creepster&family=Cinzel:wght@400;600&display=swap');

    .gradio-container {
        background:
            linear-gradient(180deg, rgba(10,0,0,0.95) 0%, rgba(26,0,0,0.9) 50%, rgba(10,5,5,0.95) 100%),
            repeating-linear-gradient(90deg, transparent, transparent 2px, rgba(0,0,0,0.3) 2px, rgba(0,0,0,0.3) 4px),
            url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><filter id="noise"><feTurbulence baseFrequency="0.9" /></filter><rect width="100" height="100" filter="url(%23noise)" opacity="0.05"/></svg>') !important;
        font-family: 'Cinzel', 'Georgia', serif !important;
        position: relative;
    }

    .gradio-container::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: radial-gradient(ellipse at center, transparent 0%, rgba(0,0,0,0.7) 100%);
        pointer-events: none;
        z-index: 0;
    }

    h1 {
        color: #8b0000 !important;
        text-shadow:
            0 0 10px rgba(139,0,0,0.8),
            0 0 20px rgba(139,0,0,0.6),
            3px 3px 6px rgba(0,0,0,0.9),
            0 0 40px rgba(220,20,60,0.4);
        font-family: 'Creepster', 'Georgia', cursive !important;
        letter-spacing: 4px;
        font-size: 3em !important;
        animation: flicker 3s infinite alternate;
    }

    @keyframes flicker {
        0%, 100% { opacity: 1; text-shadow: 0 0 10px rgba(139,0,0,0.8), 0 0 20px rgba(139,0,0,0.6), 3px 3px 6px rgba(0,0,0,0.9); }
        50% { opacity: 0.95; text-shadow: 0 0 15px rgba(139,0,0,1), 0 0 25px rgba(139,0,0,0.8), 3px 3px 6px rgba(0,0,0,0.9); }
    }

    h2, h3 {
        color: #b91c1c !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.9), 0 0 10px rgba(185,28,28,0.5);
        font-family: 'Cinzel', 'Georgia', serif !important;
        letter-spacing: 3px;
        border-bottom: 1px solid rgba(139,0,0,0.3);
        padding-bottom: 8px;
    }

    .tabs button {
        background: linear-gradient(180deg, #1a0f0f 0%, #0a0000 100%) !important;
        border: 1px solid #44403c !important;
        color: #d6d3d1 !important;
        transition: all 0.3s ease;
        font-family: 'Cinzel', serif !important;
        letter-spacing: 1px;
    }

    .tabs button:hover {
        background: linear-gradient(180deg, #2a0f0f 0%, #1a0000 100%) !important;
        border-color: #8b0000 !important;
        box-shadow: 0 0 15px rgba(139,0,0,0.5);
    }

    .tabs button[aria-selected="true"] {
        background: linear-gradient(180deg, #8b0000 0%, #5a0000 100%) !important;
        border-color: #dc2626 !important;
        color: #fef2f2 !important;
        box-shadow:
            0 0 20px rgba(139,0,0,0.6),
            inset 0 0 10px rgba(0,0,0,0.5);
    }

    .gr-button {
        background: linear-gradient(180deg, #7c2d12 0%, #5a1a0a 100%) !important;
        border: 1px solid #8b0000 !important;
        color: #fef2f2 !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
        transition: all 0.3s ease;
        font-family: 'Cinzel', serif !important;
        letter-spacing: 1px;
    }

    .gr-button:hover {
        background: linear-gradient(180deg, #8b0000 0%, #6a0000 100%) !important;
        box-shadow: 0 0 20px rgba(139,0,0,0.7), 0 5px 15px rgba(0,0,0,0.5);
        transform: translateY(-2px);
    }

    .gr-button-primary {
        background: linear-gradient(180deg, #991b1b 0%, #7f1d1d 100%) !important;
        border: 2px solid #dc2626 !important;
        box-shadow: 0 0 15px rgba(153,27,27,0.5);
    }

    .gr-button-stop {
        background: linear-gradient(180deg, #450a0a 0%, #1a0000 100%) !important;
        border: 2px solid #7f1d1d !important;
        animation: pulse-danger 2s infinite;
    }

    @keyframes pulse-danger {
        0%, 100% { box-shadow: 0 0 10px rgba(127,29,29,0.5); }
        50% { box-shadow: 0 0 25px rgba(127,29,29,0.9), 0 0 40px rgba(220,38,38,0.5); }
    }

    .gr-textbox, .gr-dropdown {
        background: rgba(20,10,10,0.8) !important;
        border: 1px solid #44403c !important;
        color: #e7e5e4 !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.5);
    }

    .gr-textbox:focus, .gr-dropdown:focus {
        border-color: #8b0000 !important;
        box-shadow: 0 0 15px rgba(139,0,0,0.4), inset 0 2px 4px rgba(0,0,0,0.5);
    }

    .gr-group, .gr-box {
        background: rgba(15,5,5,0.6) !important;
        border: 1px solid rgba(68,64,60,0.5) !important;
        border-radius: 8px !important;
        box-shadow:
            0 4px 6px rgba(0,0,0,0.5),
            inset 0 1px 2px rgba(139,0,0,0.1);
    }

    .gr-accordion {
        background: rgba(26,10,10,0.7) !important;
        border: 1px solid rgba(139,0,0,0.3) !important;
        border-radius: 6px;
    }

    label {
        color: #fca5a5 !important;
        font-family: 'Cinzel', serif !important;
        letter-spacing: 1px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
    }

    .markdown {
        color: #d6d3d1 !important;
    }

    .warning-text {
        color: #fca5a5 !important;
        font-style: italic;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.8), 0 0 10px rgba(252,165,165,0.3);
    }

    /* Effet de brouillard fantomatique */
    @keyframes ghost-float {
        0%, 100% { opacity: 0.05; transform: translateY(0px); }
        50% { opacity: 0.15; transform: translateY(-20px); }
    }

    .gradio-container::after {
        content: '';
        position: fixed;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(139,0,0,0.03) 0%, transparent 50%);
        animation: ghost-float 10s infinite ease-in-out;
        pointer-events: none;
        z-index: 1;
    }
    """

    with gr.Blocks(title=settings.APP_NAME, theme=custom_theme, css=custom_css) as demo:
        gr.Markdown(f"# 🔍 {settings.APP_NAME} 🔪")
        gr.Markdown("*Un mystère mortel vous attend dans votre propre lieu...*")

        # Rules section (collapsible)
        with gr.Accordion("📖 Règles du Jeu & Guide", open=False):
            gr.Markdown(
                """
            ## 🎯 Objectif
            Soyez le premier détective à résoudre le meurtre en identifiant correctement :
            - **Le meurtrier** (personnage)
            - **L'arme du crime** (arme)
            - **Le lieu du crime** (pièce)

            ## 🎮 Étapes de Jeu

            ### 1️⃣ Création de la Partie
            - Un joueur crée la partie en définissant 6-12 lieux personnalisés
            - Partagez le **Code d'Enquête** avec les autres détectives

            ### 2️⃣ Rejoindre l'Enquête
            - Les détectives rejoignent avec le code partagé (min. 3 joueurs)
            - Le créateur lance l'enquête quand tous sont prêts

            ### 3️⃣ Distribution des Cartes
            - Une solution secrète est créée (1 personnage + 1 arme + 1 lieu)
            - Les cartes restantes sont distribuées équitablement entre les joueurs
            - Vous voyez vos propres cartes = ces éléments **NE SONT PAS** la solution

            ### 4️⃣ Votre Tour
            Trois actions possibles :

            **💭 Proposer une Théorie** (Suggestion)
            - Proposez une combinaison personnage + arme + lieu
            - Les autres joueurs essaient de réfuter en montrant UNE carte correspondante
            - Seul VOUS voyez la carte révélée
            - Utilisez cela pour éliminer des possibilités

            **⚡ Accusation Finale**
            - Si vous pensez connaître la solution, faites une accusation
            - ✅ **Correct** = Vous gagnez immédiatement !
            - ❌ **Faux** = Vous êtes éliminé de l'enquête (mais pouvez encore réfuter)

            **⏭️ Passer le Tour**
            - Passez votre tour si vous n'avez rien à proposer

            ## 🏆 Conditions de Victoire
            - Premier joueur à faire une **accusation correcte**
            - Dernier joueur actif si tous les autres sont éliminés

            ## 💡 Conseils Stratégiques
            - Notez les cartes que vous voyez (sur papier)
            - Déduisez les cartes des autres joueurs par élimination
            - Ne faites pas d'accusation tant que vous n'êtes pas sûr !
            - Les suggestions peuvent forcer les joueurs à révéler des informations

            ## 🤖 Mode IA Narrateur (optionnel)
            Active une narration générée par IA incarnée dans Desland, un vieux jardinier mystérieux qui semble toujours en savoir plus qu'il ne devrait... Il se trompe souvent sur son nom (Leland? Non, c'est Desland...) et parle de manière étrangement suspicieuse, comme s'il cachait quelque chose de très sombre.
            """
            )

        with gr.Tab("🕯️ Créer une Partie"):
            gr.Markdown("### 🎮 Créer Votre Enquête Personnalisée")
            gr.Markdown("*Créez votre propre manoir, vos suspects et vos armes...*")

            with gr.Group():
                game_name_input = gr.Textbox(
                    label="🎭 Titre de l'enquête",
                    placeholder="Meurtre au Coworking",
                    info="Donnez un titre à votre affaire",
                )

                from models import NarrativeTone
                narrative_tone_dropdown = gr.Dropdown(
                    label="🎨 Tonalité narrative",
                    choices=[tone.value for tone in NarrativeTone],
                    value=NarrativeTone.SERIOUS.value,
                    info="Choisissez l'ambiance du jeu",
                )

                custom_prompt_input = gr.Textbox(
                    label="✍️ Prompt personnalisé (optionnel)",
                    placeholder="Style Agatha Christie avec humour noir...",
                    lines=2,
                    info="Personnalisez le style narratif de l'IA",
                )

            with gr.Group():
                gr.Markdown("#### 🏠 Configuration du Plateau")
                gr.Markdown("**Important** : L'ordre des pièces définit le plateau de jeu (circuit circulaire)")

                rooms_input = gr.Textbox(
                    label=f"🚪 Lieux ({settings.MIN_ROOMS}-{settings.MAX_ROOMS}) - DANS L'ORDRE",
                    placeholder="Cuisine, Toit, Salle serveurs, Cafétéria, Bureau, Salle de réunion",
                    lines=5,
                    info="⚠️ L'ORDRE EST IMPORTANT ! Les joueurs se déplaceront dans cet ordre (circuit). Une ligne = une pièce.",
                )

                gr.Markdown(
                    """
                    💡 **Exemple de circuit** :
                    ```
                    1. Cuisine (départ)
                    2. Salon
                    3. Bureau
                    4. Chambre
                    5. Garage
                    6. Jardin
                    → retour à Cuisine (circuit fermé)
                    ```
                    Les joueurs avancent dans cet ordre selon les dés.
                    """
                )

            with gr.Group():
                gr.Markdown("#### 🎭 Éléments du Mystère")

                suspects_input = gr.Textbox(
                    label="👤 Suspects (min. 3)",
                    placeholder="Claire, Pierre, Daniel, Marie, Thomas, Sophie",
                    lines=2,
                    info="Qui pourrait être le coupable ?",
                )

                weapons_input = gr.Textbox(
                    label="🔪 Armes (min. 3)",
                    placeholder="Clé USB, Capsule de café, Câble HDMI, Agrafeuse, Souris d'ordinateur, Plante verte",
                    lines=2,
                    info="Quelle arme a été utilisée ?",
                )

            use_ai_checkbox = gr.Checkbox(
                label="🤖 Activer le Narrateur IA - Desland (le jardinier sarcastique)",
                value=False,
                visible=settings.USE_OPENAI,
                info="Desland commente vos actions avec sarcasme et suspicion...",
            )

            create_btn = gr.Button(
                "🎬 Créer l'Enquête", variant="primary", size="lg"
            )
            create_output = gr.Textbox(
                label="📋 Résultat", lines=5, show_copy_button=True
            )
            game_id_display = gr.Textbox(
                label="🔑 Code d'Enquête (à partager)",
                interactive=False,
                show_copy_button=True,
            )

            create_btn.click(
                create_game,
                inputs=[
                    game_name_input,
                    narrative_tone_dropdown,
                    custom_prompt_input,
                    rooms_input,
                    weapons_input,
                    suspects_input,
                    use_ai_checkbox
                ],
                outputs=[create_output, game_id_display],
            )

        with gr.Tab("🕵️ Rejoindre"):
            gr.Markdown("### 👥 Entrer sur la Scène de Crime")
            gr.Markdown("*Rassemblez vos confrères détectives...*")

            with gr.Group():
                join_game_id = gr.Textbox(
                    label="🔑 Code d'Enquête",
                    placeholder="ABC123",
                    info="Code fourni par le créateur de la partie",
                )

                join_player_name = gr.Textbox(
                    label="🎩 Nom du Détective",
                    placeholder="Chnawax Masquée",
                    info="Votre nom d'enquêteur",
                )

                join_btn = gr.Button(
                    "🚪 Rejoindre l'Enquête", variant="primary", size="lg"
                )
                join_output = gr.Textbox(
                    label="📋 Statut", lines=3, show_copy_button=True
                )

                join_btn.click(
                    join_game,
                    inputs=[join_game_id, join_player_name],
                    outputs=join_output,
                )

            gr.Markdown("---")
            gr.Markdown("### 🎬 Lancer l'Enquête")
            gr.Markdown(
                "*Une fois que tous les détectives sont présents (min. 3 poupouilles)*"
            )

            with gr.Group():
                start_game_id = gr.Textbox(
                    label="🔑 Code d'Enquête",
                    placeholder="ABC123",
                    info="Seul le chnawax originel (le créateur) peut démarrer la partie",
                )

                start_btn = gr.Button(
                    "⚡ Démarrer le Mystère", variant="secondary", size="lg"
                )
                start_output = gr.Textbox(label="📋 Statut", lines=2)

                start_btn.click(start_game, inputs=start_game_id, outputs=start_output)

        with gr.Tab("🔎 Enquêter"):
            gr.Markdown("### 🕹️ Tableau de Jeu")
            gr.Markdown("*Lancez les dés, déplacez-vous, et menez l'enquête...*")

            with gr.Group():
                refresh_btn = gr.Button(
                    "🔄 Actualiser le Dossier", size="lg", variant="secondary"
                )
                game_view = gr.Textbox(
                    label="🗂️ État de la Partie",
                    lines=20,
                    max_lines=30,
                    show_copy_button=True,
                    info="Cliquez sur Actualiser pour voir l'état actuel",
                )

                refresh_btn.click(get_player_view, outputs=game_view)

            gr.Markdown("---")
            gr.Markdown("### 🎲 Votre Tour")
            gr.Markdown("**Étape 1 :** Lancez les dés pour vous déplacer")

            with gr.Group():
                roll_btn = gr.Button(
                    "🎲 Lancer les Dés", variant="primary", size="lg"
                )
                move_output = gr.Textbox(
                    label="📍 Déplacement", lines=3
                )

                roll_btn.click(roll_and_move, outputs=move_output)

            gr.Markdown("---")
            gr.Markdown("### 💭 Faire une Suggestion")
            gr.Markdown("**Étape 2 :** Faites une suggestion *dans la pièce où vous êtes*")

            with gr.Group():
                with gr.Row():
                    suggest_character = gr.Dropdown(
                        label="👤 Suspect",
                        choices=[],  # Will be populated from game
                        info="Qui est le coupable ?",
                    )
                    suggest_weapon = gr.Dropdown(
                        label="🔪 Arme",
                        choices=[],  # Will be populated from game
                        info="Quelle arme ?",
                    )
                    suggest_room = gr.Dropdown(
                        label="🚪 Lieu",
                        choices=[],  # Will be populated from game
                        info="Dans quel lieu ?",
                    )

                suggest_btn = gr.Button(
                    "💭 Faire la Suggestion", variant="primary", size="lg"
                )
                suggest_output = gr.Textbox(
                    label="🗨️ Résultat", lines=5, show_copy_button=True
                )

                suggest_btn.click(
                    make_suggestion,
                    inputs=[suggest_character, suggest_weapon, suggest_room],
                    outputs=suggest_output,
                )

            gr.Markdown("---")
            gr.Markdown("### ⚖️ Accusation Finale")
            gr.Markdown(
                "⚠️ **ATTENTION :** Une fausse accusation vous élimine !"
            )

            with gr.Group():
                with gr.Row():
                    accuse_character = gr.Dropdown(
                        label="👤 Le Coupable",
                        choices=[],
                        info="Qui ?",
                    )
                    accuse_weapon = gr.Dropdown(
                        label="🔪 L'Arme",
                        choices=[],
                        info="Avec quoi ?",
                    )
                    accuse_room = gr.Dropdown(
                        label="🚪 Le Lieu",
                        choices=[],
                        info="Où ?",
                    )

                accuse_btn = gr.Button(
                    "⚡ ACCUSER", variant="stop", size="lg"
                )
                accuse_output = gr.Textbox(
                    label="⚖️ Verdict", lines=5, show_copy_button=True
                )

                accuse_btn.click(
                    make_accusation,
                    inputs=[accuse_character, accuse_weapon, accuse_room],
                    outputs=accuse_output,
                )

            gr.Markdown("---")

            with gr.Group():
                pass_btn = gr.Button(
                    "⏭️ Passer Mon Tour", variant="secondary", size="lg"
                )
                pass_output = gr.Textbox(label="📋 Statut", lines=1)

                pass_btn.click(pass_turn, outputs=pass_output)

    return demo


def run_fastapi():
    """
    Run FastAPI server in a separate thread.
    """
    from api import app

    uvicorn.run(app, host=settings.HOST, port=settings.PORT, log_level="info")


if __name__ == "__main__":
    # IS_HUGGINGFACE is already defined at the top of the file

    # Note: We're always in HUGGINGFACE mode (direct backend calls)
    # No need for FastAPI server

    # Create and launch Gradio interface
    demo = create_gradio_interface()

    # Launch on available port
    demo.launch(
        server_name="127.0.0.1",
        server_port=7862,
        share=False,
        show_error=True,
    )
