import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createQuickGame } from '../api'

function Home() {
  const [playerName, setPlayerName] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleCreateGame = async () => {
    if (!playerName.trim()) {
      alert('Veuillez entrer votre nom')
      return
    }

    setLoading(true)
    try {
      const response = await createQuickGame(playerName.trim())
      navigate(`/game/${response.game_id}/${response.player_id}`)
    } catch (error) {
      alert('Erreur lors de la création de la partie')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-md w-full space-y-8 bg-dark-800 p-8 rounded-lg shadow-2xl border border-dark-700">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-accent-400 mb-2">🔍 Cluedo Custom</h1>
          <p className="text-dark-300">Créez votre partie et invitez vos amis</p>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-dark-200 mb-2">
              Votre nom
            </label>
            <input
              type="text"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleCreateGame()}
              placeholder="Entrez votre nom"
              className="w-full px-4 py-3 bg-dark-700 border border-dark-600 rounded-lg text-white placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-accent-500"
            />
          </div>

          <button
            onClick={handleCreateGame}
            disabled={loading}
            className="w-full py-3 px-4 bg-accent-600 hover:bg-accent-700 disabled:bg-dark-600 text-white font-semibold rounded-lg transition-colors"
          >
            {loading ? 'Création...' : '🎮 Créer une partie'}
          </button>

          <div className="text-center pt-4">
            <button
              onClick={() => navigate('/join')}
              className="text-accent-400 hover:text-accent-300 underline"
            >
              Rejoindre une partie existante
            </button>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-dark-700 text-center text-sm text-dark-400">
          <p>Thème par défaut : Manoir Classique</p>
          <p className="mt-1">3-6 joueurs recommandés</p>
        </div>
      </div>
    </div>
  )
}

export default Home
