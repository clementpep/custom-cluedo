import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { joinGame } from '../api'

function Join() {
  const [gameCode, setGameCode] = useState('')
  const [playerName, setPlayerName] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleJoinGame = async () => {
    if (!gameCode.trim() || !playerName.trim()) {
      alert('Veuillez remplir tous les champs')
      return
    }

    setLoading(true)
    try {
      const response = await joinGame(gameCode.trim(), playerName.trim())
      navigate(`/game/${response.game_id}/${response.player_id}`)
    } catch (error) {
      alert('Erreur : ' + (error.response?.data?.detail || 'Impossible de rejoindre la partie'))
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-md w-full space-y-8 bg-dark-800 p-8 rounded-lg shadow-2xl border border-dark-700">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-accent-400 mb-2">🚪 Rejoindre une partie</h1>
          <p className="text-dark-300">Entrez le code partagé par votre hôte</p>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-dark-200 mb-2">
              Code de partie
            </label>
            <input
              type="text"
              value={gameCode}
              onChange={(e) => setGameCode(e.target.value.toUpperCase())}
              placeholder="Ex: ABC4"
              maxLength={4}
              className="w-full px-4 py-3 bg-dark-700 border border-dark-600 rounded-lg text-white text-center text-2xl font-mono placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-accent-500 uppercase"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-200 mb-2">
              Votre nom
            </label>
            <input
              type="text"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleJoinGame()}
              placeholder="Entrez votre nom"
              className="w-full px-4 py-3 bg-dark-700 border border-dark-600 rounded-lg text-white placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-accent-500"
            />
          </div>

          <button
            onClick={handleJoinGame}
            disabled={loading}
            className="w-full py-3 px-4 bg-accent-600 hover:bg-accent-700 disabled:bg-dark-600 text-white font-semibold rounded-lg transition-colors"
          >
            {loading ? 'Connexion...' : '✅ Rejoindre'}
          </button>

          <div className="text-center pt-4">
            <button
              onClick={() => navigate('/')}
              className="text-accent-400 hover:text-accent-300 underline"
            >
              ← Retour à l'accueil
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Join
