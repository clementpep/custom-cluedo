import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const gameAPI = {
  // Get available themes
  getThemes: () => api.get('/themes'),

  // Quick create with defaults
  quickCreate: (theme, playerName) =>
    api.post('/games/quick-create', { theme, player_name: playerName }),

  // Join existing game
  join: (gameId, playerName) =>
    api.post('/games/join', { game_id: gameId, player_name: playerName }),

  // Start game
  start: (gameId) => api.post(`/games/${gameId}/start`),

  // Get game state
  getState: (gameId, playerId) => api.get(`/games/${gameId}/state/${playerId}`),

  // Roll dice
  rollDice: (gameId, playerId) =>
    api.post(`/games/${gameId}/roll`, { player_id: playerId }),

  // Make suggestion
  suggest: (gameId, playerId, suspect, weapon, room) =>
    api.post(`/games/${gameId}/suggest`, {
      player_id: playerId,
      suspect,
      weapon,
      room,
    }),

  // Make accusation
  accuse: (gameId, playerId, suspect, weapon, room) =>
    api.post(`/games/${gameId}/accuse`, {
      player_id: playerId,
      suspect,
      weapon,
      room,
    }),

  // Pass turn
  pass: (gameId, playerId) =>
    api.post(`/games/${gameId}/pass`, { player_id: playerId }),
};

export default api;
