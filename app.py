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


def create_game(game_name: str, rooms_text: str, use_ai: bool):
    """
    Create a new game.
    """
    if not game_name or not rooms_text:
        return "❌ Ekelesbikes ! Fournissez un nom d'enquête et une liste de pièces", ""

    # Parse rooms (comma or newline separated)
    rooms = [r.strip() for r in rooms_text.replace("\n", ",").split(",") if r.strip()]

    if len(rooms) < settings.MIN_ROOMS:
        return (
            f"❌ Koikoubaiseyyyyy ! Il faut au moins {settings.MIN_ROOMS} pièces",
            "",
        )

    if len(rooms) > settings.MAX_ROOMS:
        return (
            f"❌ Triple monstre coucouuuuu ! Maximum {settings.MAX_ROOMS} pièces autorisées",
            "",
        )

    try:
        if IS_HUGGINGFACE:
            # Direct backend call
            from game_manager import game_manager
            from models import CreateGameRequest

            request = CreateGameRequest(game_name=game_name, rooms=rooms, use_ai=use_ai)
            game = game_manager.create_game(request)

            # Generate AI scenario if enabled
            if game.use_ai and settings.USE_OPENAI:
                from game_engine import DEFAULT_CHARACTERS
                from ai_service import ai_service
                import asyncio

                try:
                    scenario = asyncio.run(
                        ai_service.generate_scenario(game.rooms, DEFAULT_CHARACTERS)
                    )
                    if scenario:
                        game.scenario = scenario
                        game_manager.save_games()
                except:
                    pass  # AI is optional

            state.game_id = game.game_id
            return (
                f"✅ Enquête créée avec succès ! En alicrampté, les coicoubaca sont de sortie...\n\n"
                f"🔑 Code d'Enquête : {game.game_id}\n\n"
                f"📤 Partagez ce code avec les autres poupouilles masquées pour qu'elles puissent vous rejoindre en alicrampté.\n\n"
                f"ℹ️ Minimum {settings.MIN_PLAYERS} péchailloux requis pour démarrer (sinon c'est les fourlestourtes et les bourbillats).",
                game.game_id,
            )
        else:
            # HTTP API call (local mode)
            response = requests.post(
                f"{API_BASE}/games/create",
                json={"game_name": game_name, "rooms": rooms, "use_ai": use_ai},
                timeout=5,
            )

            if response.status_code == 200:
                data = response.json()
                state.game_id = data["game_id"]
                return (
                    f"✅ Enquête créée avec succès ! En alicrampté, les coicoubaca sont de sortie...\n\n"
                    f"🔑 Code d'Enquête : {data['game_id']}\n\n"
                    f"📤 Partagez ce code avec les autres joueurs pour qu'ils puissent rejoindre.\n\n"
                    f"ℹ️ Minimum {settings.MIN_PLAYERS} joueurs requis pour démarrer.",
                    data["game_id"],
                )
            else:
                return (
                    f"❌ All RS5, erreur réseau : {response.json().get('detail', 'Erreur inconnue')}",
                    "",
                )

    except Exception as e:
        return f"❌ Yamete coudasai ! Erreur lors de la création : {str(e)}", ""


def join_game(game_id: str, player_name: str):
    """
    Join an existing game.
    """
    if not game_id or not player_name:
        return "❌ Yamete coudasai ! Fournissez le code d'enquête et votre nom de tchoupinoux masqué !"

    try:
        game_id = game_id.strip().upper()
        player_name = player_name.strip()

        if IS_HUGGINGFACE:
            # Direct backend call
            from game_manager import game_manager
            from models import GameStatus

            game = game_manager.get_game(game_id)
            if not game:
                return "❌ Erreur réseau ! Enquête introuvable... C'est Leland (non c'est Desland)"

            if game.status != GameStatus.WAITING:
                return "❌ Armankaboul ! Les chnawax masqués jouent déjà !"

            if game.is_full():
                return "❌ Chat 4, 3 entre chat 4 et 1 brisé ! Trop de poupouilles dans l'enquête..."

            player = game_manager.join_game(game_id, player_name)
            if not player:
                return "❌ Une poupée en pénitence calisse ! Impossible de rejoindre l'enquête !"

            state.game_id = game_id
            state.player_id = player.id
            state.player_name = player_name

            return (
                f"✅ Enquête rejointe avec succès !\n\n"
                f"👋 Bienvenue, {player_name} !\n\n"
                f"⏳ Attendez que le chnawax originel (le créateur) démarre la partie...\n"
                f"📖 Allez dans l'onglet 🔎 Enquêter pour voir l'état de la partie."
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
                return "❌ Erreur ! Pas assez de tchoupinoux masqués pour commencer la partie !"

            return (
                f"🩸 LE MASSACRE COMMENCE ! Triple monstre coucouuuuu !\n\n"
                f"🎲 Les cartes ont été distribuées.\n"
                f"🔪 Tous les joueurs peuvent maintenant consulter leurs cartes et commencer à jouer.\n\n"
                f"➡️ Allez dans l'onglet 🔎 Enquêter pour voir votre dossier."
            )
        else:
            # HTTP API call (local mode)
            response = requests.post(f"{API_BASE}/games/{game_id}/start", timeout=5)

            if response.status_code == 200:
                return (
                    f"🩸 LE MASSACRE COMMENCE ! Triple monstre coucouuuuu !\n\n"
                    f"🎲 Les cartes ont été distribuées.\n"
                    f"🔪 Tous les joueurs peuvent maintenant consulter leurs cartes et commencer à jouer.\n\n"
                    f"➡️ Allez dans l'onglet 🔎 Enquêter pour voir votre dossier."
                )
            else:
                return f"❌ All RS5 erreur réseau : {response.json().get('detail', 'Erreur inconnue')}"

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
            other_players = [
                {"name": p.name, "is_active": p.is_active, "card_count": len(p.cards)}
                for p in game.players
                if p.id != state.player_id
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
                "other_players": other_players,
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
        output.append(f"═══ 🩸 {data['game_name']} - LE CARNAGE SANGLANT 🩸 ═══\n")

        status_map = {
            "waiting": "⏳ Les poupouilles masquées arrivent...",
            "in_progress": "🔪 CARNAGE EN COURS",
            "finished": "💀 MASSACRE TERMINÉ - Un chnawax a gagné",
        }
        output.append(f"📊 Statut : {status_map.get(data['status'], data['status'])}\n")

        if data.get("scenario"):
            output.append(f"\n📜 Scénario :\n{data['scenario']}\n")

        output.append(f"\n━━━ 🃏 VOS CARTES ━━━")
        output.append("(Ces éléments NE SONT PAS la solution)")
        for card in data["my_cards"]:
            output.append(f"  🔸 {card}")

        output.append(f"\n━━━ ℹ️ INFORMATIONS DE JEU ━━━")
        output.append(f"🚪 Lieux : {', '.join(data['rooms'])}")
        output.append(f"👤 Personnages : {', '.join(data['characters'])}")
        output.append(f"🔪 Armes : {', '.join(data['weapons'])}")

        output.append(f"\n━━━ 👥 DÉTECTIVES ━━━")
        for player in data["other_players"]:
            status_icon = "✅" if player["is_active"] else "❌"
            output.append(
                f"  {status_icon} {player['name']} ({player['card_count']} cartes)"
            )

        if data["current_turn"]:
            turn_marker = (
                "👉 C'EST TON TOUR MON PÉCHAILLOUX !" if data["is_my_turn"] else ""
            )
            output.append(f"\n━━━ 🎯 TOUR ACTUEL ━━━")
            output.append(f"🎲 {data['current_turn']} {turn_marker}")

        if data.get("winner"):
            output.append(
                f"\n\n🏆🏆🏆 QUOICOUBAIDEYYYYY ! VAINQUEUR : {data['winner']} 🏆🏆🏆"
            )

        if data["recent_turns"]:
            output.append(f"\n━━━ 📰 ACTIONS RÉCENTES ━━━")
            for turn in data["recent_turns"][-5:]:
                output.append(f"  • {turn['player_name']}: {turn['action']}")
                if turn.get("details"):
                    output.append(f"    ↪ {turn['details']}")

        return "\n".join(output)

    except Exception as e:
        return f"❌ Erreur réseau (fourlestourtes et les bourbillats) : {str(e)}"


def make_suggestion(character: str, weapon: str, room: str):
    """
    Make a suggestion.
    """
    if not state.game_id or not state.player_id:
        return "❌ Ekelesbikes ! Vous n'êtes pas dans une enquête"

    if not all([character, weapon, room]):
        return "❌ Eskilibass (I'm a spiderman), choisissez un personnage, une arme et un lieu"

    try:
        if IS_HUGGINGFACE:
            # Direct backend call
            from game_manager import game_manager
            from game_engine import GameEngine

            game = game_manager.get_game(state.game_id)

            if not game:
                return "❌ All RS5, erreur réseau ! Enquête introuvable"

            # Verify it's the player's turn
            if not GameEngine.can_player_act(game, state.player_id):
                return "❌ Yamete coudasai ! C'est pas ton tour !"

            player = next((p for p in game.players if p.id == state.player_id), None)
            if not player:
                return "❌ All RS5, erreur réseau ! Péchailloux masqué introuvable"

            can_disprove, disprover, card = GameEngine.check_suggestion(
                game, state.player_id, character, weapon, room
            )

            suggestion_text = f"Suggested: {character} with {weapon} in {room}"

            if can_disprove and disprover and card:
                message = (
                    f"{disprover} disproved the suggestion by showing: {card.name}"
                )
            else:
                message = "No one could disprove the suggestion!"

            GameEngine.add_turn_record(
                game, state.player_id, "suggest", suggestion_text
            )
            game.next_turn()
            game_manager.save_games()

            # Translate common responses
            if "disproved" in message.lower():
                return (
                    f"💭 {message}\n\n➡️ Notes cette information pour tes déductions !"
                )
            else:
                return f"💭 {message}\n\n⚠️ Aucun chnawax n'a pu réfuter ta théorie !"
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
                message = data["message"]

                # Translate common responses
                if "disproved" in message.lower():
                    return f"💭 {message}\n\n➡️ Notez cette information pour vos déductions !"
                else:
                    return f"💭 {message}\n\n⚠️ Personne n'a pu réfuter votre théorie !"
            else:
                error = response.json().get("detail", "Erreur inconnue")
                if "Not your turn" in error:
                    return "❌ Yamete coudasai ! C'est pas ton tour !"
                return f"❌ Erreur réseau (fourlestourtes et les bourbillats) : {error}"

    except Exception as e:
        return f"❌ Koikoubaiseyyyyy ! Erreur : {str(e)}"


def make_accusation(character: str, weapon: str, room: str):
    """
    Make an accusation.
    """
    if not state.game_id or not state.player_id:
        return "❌ Vous n'êtes pas dans une enquête"

    if not all([character, weapon, room]):
        return "❌ Armankaboul ! Choisissez un personnage, une arme et un lieu"

    try:
        if IS_HUGGINGFACE:
            # Direct backend call
            from game_manager import game_manager
            from game_engine import GameEngine
            from models import GameStatus

            game = game_manager.get_game(state.game_id)

            if not game:
                return "❌ All RS5, erreur réseau : Enquête introuvable"

            # Verify it's the player's turn
            if not GameEngine.can_player_act(game, state.player_id):
                return "❌ Yamete coudasai ! C'est pas ton tour !"

            player = next((p for p in game.players if p.id == state.player_id), None)
            if not player:
                return "❌ All RS5, erreur réseau : Joueur introuvable"

            accusation_text = f"Accused: {character} with {weapon} in {room}"

            is_correct, message = GameEngine.process_accusation(
                game, state.player_id, character, weapon, room
            )

            GameEngine.add_turn_record(game, state.player_id, "accuse", accusation_text)

            if not is_correct and game.status == GameStatus.IN_PROGRESS:
                game.next_turn()

            game_manager.save_games()

            # Check if win or lose
            if "wins" in message.lower() or "correct" in message.lower():
                return f"🎉🏆 {message} 🎉🏆\n\nTRIPLE MONSTRE COUCOUUUUU ! Tu as résolu le mystère ! (3 entre chat 4 et 1 brisé)"
            elif "wrong" in message.lower() or "eliminated" in message.lower():
                return f"💀 {message}\n\n😔 Fourlestourtes et les bourbillats... Tu as été éliminé calisse en pénitence siboère !\nTu peux toujours aider en réfutant les théories des autres."
            else:
                return f"⚖️ {message}"
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
                message = data["message"]

                # Check if win or lose
                if "wins" in message.lower() or "correct" in message.lower():
                    return f"🎉🏆 {message} 🎉🏆\n\nTRIPLE MONSTRE COUCOUUUUU ! Tu as résolu le mystère ! (3 entre chat 4 et 1 brisé)"
                elif "wrong" in message.lower() or "eliminated" in message.lower():
                    return f"💀 {message}\n\n😔 Fourlestourtes et les bourbillats... Tu as été éliminé calisse en pénitence siboère !\nTu peux toujours aider en réfutant les théories des autres."
                else:
                    return f"⚖️ {message}"
            else:
                error = response.json().get("detail", "Erreur inconnue")
                if "Not your turn" in error:
                    return "❌ Yamete coudasai ! C'est pas ton tour !"
                return f"❌ All RS5, erreur réseau : {error}"

    except Exception as e:
        return f"❌ Koikoubaiseyyyyy ! Erreur : {str(e)}"


def pass_turn():
    """
    Pass the current turn.
    """
    if not state.game_id or not state.player_id:
        return "❌ Eskilibass ! Vous n'êtes pas dans une enquête"

    try:
        if IS_HUGGINGFACE:
            # Direct backend call
            from game_manager import game_manager
            from game_engine import GameEngine

            game = game_manager.get_game(state.game_id)

            if not game:
                return "❌ All RS5, erreur réseau ! Enquête introuvable"

            # Verify it's the player's turn
            if not GameEngine.can_player_act(game, state.player_id):
                return "❌ Yamete coudasai ! C'est pas ton tour !"

            player = next((p for p in game.players if p.id == state.player_id), None)
            if not player:
                return "❌ All RS5, erreur réseau ! Joueur introuvable"

            # Pass turn
            GameEngine.add_turn_record(game, state.player_id, "pass", "Passed turn")
            game.next_turn()
            game_manager.save_games()

            return f"✅ Tour passé !\n\n➡️ C'est maintenant au tour de la prochaine poupouille."
        else:
            # HTTP API call (local mode)
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
                return f"✅ Tour passé !\n\n➡️ C'est maintenant au tour de la prochaine poupouille."
            else:
                error = response.json().get("detail", "Erreur inconnue")
                if "Not your turn" in error:
                    return "❌ Yamete coudasai ! C'est pas ton tour !"
                return f"❌ All RS5, erreur réseau (fourlestourtes et les bourbillats) : {error}"

    except Exception as e:
        return f"❌ Koikoubaiseyyyyy ! Erreur : {str(e)}"


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
            gr.Markdown("### 📜 Établir un Nouveau Mystère")
            gr.Markdown("*Préparez la scène d'un meurtre des plus ignobles...*")

            game_name_input = gr.Textbox(
                label="🎭 Nom de l'enquête",
                placeholder="Le Meurtre au Manoir des Poupouilles",
                info="Donnez un nom à votre affaire (ex : armankaboul)",
            )

            rooms_input = gr.Textbox(
                label=f"🚪 Lieux de la scène de crime ({settings.MIN_ROOMS}-{settings.MAX_ROOMS} pièces)",
                placeholder="Le salon des péchailloux, La chambre du Viande, Bureau des Chnawax, Le B15 des Tchoupinoux, Le jardin de la poupouille",
                lines=4,
                info="Séparez les pièces par des virgules ou des retours à la ligne",
            )

            use_ai_checkbox = gr.Checkbox(
                label="🤖 Activer le Narrateur IA - Lesland... euh non Desland",
                value=False,
                visible=settings.USE_OPENAI,
                info="Un vieux jardinier suspicieux qui semble en savoir plus qu'il n'y paraît...",
            )

            create_btn = gr.Button(
                "🩸 Commencer l'Enquête", variant="primary", size="lg"
            )
            create_output = gr.Textbox(
                label="📋 Dossier de l'Affaire", lines=5, show_copy_button=True
            )
            game_id_display = gr.Textbox(
                label="🔑 Code d'Enquête (partagez avec les autres poupouilles masquées)",
                interactive=False,
                show_copy_button=True,
            )

            create_btn.click(
                create_game,
                inputs=[game_name_input, rooms_input, use_ai_checkbox],
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
            gr.Markdown("### 📰 Tableau d'Enquête")
            gr.Markdown("*Étudiez les preuves et faites vos déductions...*")

            with gr.Group():
                refresh_btn = gr.Button(
                    "🔄 Actualiser le Dossier", size="lg", variant="secondary"
                )
                game_view = gr.Textbox(
                    label="🗂️ Dossier du Détective",
                    lines=20,
                    max_lines=30,
                    show_copy_button=True,
                    info="Cliquez sur Actualiser pour voir l'état actuel de la partie",
                )

                refresh_btn.click(get_player_view, outputs=game_view)

            gr.Markdown("---")
            gr.Markdown("### 🔮 Proposition de Théorie")
            gr.Markdown("*Testez une hypothèse auprès des autres détectives...*")

            with gr.Group():
                with gr.Row():
                    suggest_character = gr.Dropdown(
                        label="👤 Suspect",
                        choices=DEFAULT_CHARACTERS,
                        info="Choisissez un personnage",
                    )
                    suggest_weapon = gr.Dropdown(
                        label="🔪 Arme du Crime",
                        choices=DEFAULT_WEAPONS,
                        info="Choisissez une arme",
                    )
                    suggest_room = gr.Dropdown(
                        label="🚪 Lieu du Crime",
                        choices=[],  # Will be populated from game
                        info="Choisissez un lieu",
                    )

                suggest_btn = gr.Button(
                    "💭 Proposer une Théorie", variant="primary", size="lg"
                )
                suggest_output = gr.Textbox(
                    label="🗨️ Réponse", lines=3, show_copy_button=True
                )

                suggest_btn.click(
                    make_suggestion,
                    inputs=[suggest_character, suggest_weapon, suggest_room],
                    outputs=suggest_output,
                )

            gr.Markdown("---")
            gr.Markdown("### ⚖️ Accusation Finale")
            gr.Markdown(
                "### ⚠️ *Yamete cudasaï ! Une fausse accusation vous élimine de l'enquête !*"
            )

            with gr.Group():
                with gr.Row():
                    accuse_character = gr.Dropdown(
                        label="👤 Le Meurtrier",
                        choices=DEFAULT_CHARACTERS,
                        info="Qui a commis le crime ?",
                    )
                    accuse_weapon = gr.Dropdown(
                        label="🔪 L'Arme",
                        choices=DEFAULT_WEAPONS,
                        info="Avec quelle arme ?",
                    )
                    accuse_room = gr.Dropdown(
                        label="🚪 Le Lieu", choices=[], info="Dans quel lieu ?"
                    )

                accuse_btn = gr.Button(
                    "⚡ FAIRE L'ACCUSATION", variant="stop", size="lg"
                )
                accuse_output = gr.Textbox(
                    label="⚖️ Verdict", lines=3, show_copy_button=True
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

    if not IS_HUGGINGFACE:
        # Local development: run FastAPI in background
        def run_fastapi_bg():
            """Run FastAPI on port 8000 in background"""
            from api import app

            uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

        api_thread = threading.Thread(target=run_fastapi_bg, daemon=True)
        api_thread.start()

        # Wait for API to start
        time.sleep(2)

    # Create and launch Gradio interface
    demo = create_gradio_interface()

    if IS_HUGGINGFACE:
        # On Hugging Face Spaces: Gradio only on port 7860 (no FastAPI)
        demo.launch(
            server_name="0.0.0.0",
            share=False,
            show_error=True,
        )
    else:
        # Local development: Gradio on port 7861, FastAPI on 8000
        demo.launch(
            server_name="127.0.0.1",
            server_port=7861,
            share=False,
            show_error=True,
        )
