# Cluedo Custom

A web-based custom Cluedo (Clue) game that transforms real-world locations into interactive murder mystery games. Players can create games with custom room names matching their physical environment and play together in real-time.

## Features

- **Custom Room Setup**: Define your own rooms based on your real-world location (office, house, school, etc.)
- **Multi-player Support**: Up to 8 players per game
- **Real-time Gameplay**: Turn-based system with suggestions and accusations
- **AI-Enhanced Narration** (Optional): Generate atmospheric scenarios and narration using OpenAI
- **Mobile-First Interface**: Responsive design optimized for smartphone gameplay
- **Easy Deployment**: Docker-ready and compatible with Hugging Face Spaces

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd custom-cluedo
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment** (optional)
   ```bash
   cp .env.example .env
   # Edit .env to configure settings
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the interface**
   Open your browser at `http://localhost:7860`

### Docker Deployment

1. **Build the Docker image**
   ```bash
   docker build -t cluedo-custom .
   ```

2. **Run the container**
   ```bash
   docker run -p 7860:7860 cluedo-custom
   ```

   Or with environment variables:
   ```bash
   docker run -p 7860:7860 \
     -e USE_OPENAI=true \
     -e OPENAI_API_KEY=your_key_here \
     cluedo-custom
   ```

### Hugging Face Spaces Deployment

1. **Create a new Space**
   - Go to [Hugging Face Spaces](https://huggingface.co/spaces)
   - Click "Create new Space"
   - Choose "Gradio" as the SDK

2. **Upload files**
   - Upload all project files to your Space
   - Ensure `app.py` is the main entry point

3. **Configure secrets** (for AI mode)
   - Go to Settings → Repository secrets
   - Add `OPENAI_API_KEY` if using AI features

4. **Set environment variables** in Space settings:
   ```
   USE_OPENAI=true
   APP_NAME=Cluedo Custom
   MAX_PLAYERS=8
   ```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name displayed in the interface | `Cluedo Custom` |
| `MAX_PLAYERS` | Maximum number of players per game | `8` |
| `USE_OPENAI` | Enable AI-generated content (true/false) | `false` |
| `OPENAI_API_KEY` | OpenAI API key (required if USE_OPENAI=true) | `""` |

## How to Play

### 1. Create a Game

- Navigate to the "Create Game" tab
- Enter a game name
- List 6-12 room names that match your real-world location
  - Example: `Kitchen, Living Room, Bedroom, Office, Garage, Garden`
- Optionally enable AI narration
- Click "Create Game" and share the Game ID with other players

### 2. Join a Game

- Navigate to the "Join Game" tab
- Enter the Game ID provided by the game creator
- Enter your player name
- Click "Join Game"

### 3. Start the Game

- Once all players have joined (minimum 3 players)
- The game creator clicks "Start Game"
- Cards are automatically distributed to all players

### 4. Play Your Turn

- Navigate to the "Play" tab
- Click "Refresh Game State" to see current status
- When it's your turn:
  - **Make a Suggestion**: Choose a character, weapon, and room. Other players will try to disprove it.
  - **Make an Accusation**: If you think you know the solution. Warning: wrong accusations eliminate you!
  - **Pass Turn**: Skip to the next player

### 5. Win the Game

- The first player to make a correct accusation wins
- Or be the last player standing if others are eliminated

## Game Rules

### Setup

- Each game has:
  - 6 default characters (Miss Scarlett, Colonel Mustard, Mrs. White, etc.)
  - 6 default weapons (Candlestick, Knife, Lead Pipe, etc.)
  - Custom rooms defined by the players

### Solution

- At the start, one character, one weapon, and one room are randomly selected as the secret solution
- All other cards are distributed evenly among players

### Gameplay

1. **Suggestions**:
   - Player suggests a character, weapon, and room combination
   - Other players (clockwise) try to disprove by showing one matching card
   - Only the suggesting player sees the card shown

2. **Accusations**:
   - Player makes a final accusation of the solution
   - If correct: player wins immediately
   - If incorrect: player is eliminated and cannot act further

3. **Victory**:
   - First player with correct accusation wins
   - If all others are eliminated, the last remaining player wins

## AI Mode

When enabled (`USE_OPENAI=true`), the application generates:

- **Scenario Introduction**: Atmospheric setup describing the mystery in your chosen location
- **Turn Narration** (optional): Brief narrative elements during gameplay

AI features use GPT-3.5-turbo with:
- Low temperature for consistency
- 3-second timeout per request
- Graceful fallback if unavailable

## Project Structure

```
custom-cluedo/
├── app.py              # Main application (Gradio interface)
├── api.py              # FastAPI backend routes
├── config.py           # Configuration and settings
├── models.py           # Data models (Pydantic)
├── game_engine.py      # Core game logic
├── game_manager.py     # Game state management
├── ai_service.py       # OpenAI integration
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker configuration
├── .env.example        # Environment variables template
└── README.md           # This file
```

## Technical Details

### Backend

- **FastAPI**: REST API for game management
- **In-memory storage**: Games stored in memory with JSON persistence
- **Pydantic models**: Type-safe data validation

### Frontend

- **Gradio**: Interactive web interface
- **Mobile-optimized**: Responsive design with large touch targets
- **Real-time updates**: Manual refresh for game state (polling-based)

### Storage

- Games are stored in `games.json` for persistence
- Data is lost when container restarts (suitable for casual play)
- No database required

## API Endpoints

- `GET /` - Health check
- `POST /games/create` - Create new game
- `POST /games/join` - Join existing game
- `POST /games/{game_id}/start` - Start game
- `GET /games/{game_id}` - Get full game state
- `GET /games/{game_id}/player/{player_id}` - Get player-specific view
- `POST /games/{game_id}/action` - Perform game action
- `GET /games/list` - List active games
- `DELETE /games/{game_id}` - Delete game

## Limitations

- Maximum 8 players per game (configurable)
- Minimum 3 players to start
- 6-12 custom rooms required
- No persistent database (games reset on restart)
- AI features require OpenAI API key and have rate limits

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests (when implemented)
pytest
```

### Code Style

- Code documented in English
- Type hints using Pydantic models
- Follows PEP 8 guidelines

## Troubleshooting

### Port 7860 already in use

Change the port in `config.py` or use environment variable:
```bash
PORT=8000 python app.py
```

### AI features not working

- Verify `USE_OPENAI=true` is set
- Check `OPENAI_API_KEY` is valid
- Ensure OpenAI API is accessible
- Check API rate limits

### Game state not updating

- Click "Refresh Game State" button
- Check network connection to API
- Verify game ID and player ID are correct

## License

This project is provided as-is for educational and recreational purposes.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Support

For issues and questions:
- Create an issue on GitHub
- Check existing documentation
- Review API endpoint responses for error details
