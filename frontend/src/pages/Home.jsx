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
    <div className="min-h-screen bg-haunted-gradient flex items-center justify-center p-4 relative overflow-hidden">
      {/* Animated fog effect */}
      <div className="absolute inset-0 bg-fog-gradient opacity-20 animate-pulse-slow pointer-events-none"></div>

      {/* Floating ghost elements */}
      <div className="absolute top-20 left-10 w-32 h-32 bg-haunted-ghost opacity-5 rounded-full blur-3xl animate-float"></div>
      <div className="absolute bottom-20 right-10 w-40 h-40 bg-haunted-purple opacity-5 rounded-full blur-3xl animate-float" style={{animationDelay: '2s'}}></div>

      <div className="max-w-md w-full space-y-8 bg-black/60 backdrop-blur-md p-8 rounded-lg shadow-2xl border-2 border-haunted-blood/30 animate-fade-in relative z-10">
        <div className="text-center">
          <h1 className="text-6xl font-bold text-haunted-blood mb-2 animate-flicker drop-shadow-[0_0_10px_rgba(139,0,0,0.5)]">
            🕯️ Cluedo Custom
          </h1>
          <p className="text-haunted-fog/80 text-lg italic">Le manoir vous attend dans l'obscurité...</p>
          <div className="mt-2 text-xs text-haunted-ghost/50">💀 Osez-vous entrer ? 💀</div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-haunted-fog mb-2">
              Votre nom
            </label>
            <input
              type="text"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleCreateGame()}
              placeholder="Qui ose s'aventurer..."
              className="w-full px-4 py-3 bg-black/40 border-2 border-haunted-shadow rounded-lg text-haunted-fog placeholder-dark-500 focus:outline-none focus:ring-2 focus:ring-haunted-blood focus:border-haunted-blood transition-all"
            />
          </div>

          <button
            onClick={handleCreateGame}
            disabled={loading}
            className="w-full py-3 px-4 bg-haunted-blood hover:bg-red-800 disabled:bg-dark-600 disabled:opacity-50 text-white font-bold rounded-lg transition-all transform hover:scale-105 hover:shadow-[0_0_20px_rgba(139,0,0,0.5)] border border-red-900"
          >
            {loading ? '🕯️ Création...' : '🚪 Entrer dans le Manoir'}
          </button>

          <div className="text-center pt-4">
            <button
              onClick={() => navigate('/join')}
              className="text-haunted-fog/70 hover:text-haunted-blood underline transition-colors"
            >
              👻 Rejoindre une partie existante
            </button>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-haunted-shadow text-center text-sm text-haunted-fog/60">
          <p className="italic">⚰️ Thème : Meurtre au Manoir ⚰️</p>
          <p className="mt-1">3-6 âmes perdues recommandées</p>
        </div>
      </div>
    </div>
  )
}

export default Home
