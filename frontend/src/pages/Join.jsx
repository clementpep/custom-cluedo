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
    <div className="min-h-screen bg-haunted-gradient flex items-center justify-center p-4 relative overflow-hidden">
      {/* Animated fog effect */}
      <div className="absolute inset-0 bg-fog-gradient opacity-20 animate-pulse-slow pointer-events-none"></div>

      {/* Floating ghost elements */}
      <div className="absolute top-20 left-10 w-32 h-32 bg-haunted-ghost opacity-5 rounded-full blur-3xl animate-float"></div>
      <div className="absolute bottom-20 right-10 w-40 h-40 bg-haunted-purple opacity-5 rounded-full blur-3xl animate-float" style={{animationDelay: '2s'}}></div>

      <div className="max-w-md w-full space-y-8 bg-black/60 backdrop-blur-md p-8 rounded-lg shadow-2xl border-2 border-haunted-blood/30 animate-fade-in relative z-10">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-haunted-blood mb-2 animate-flicker drop-shadow-[0_0_10px_rgba(139,0,0,0.5)]">
            👻 Rejoindre la Séance
          </h1>
          <p className="text-haunted-fog/80 italic">Entrez le code maudit...</p>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-haunted-fog mb-2">
              🔮 Code de partie
            </label>
            <input
              type="text"
              value={gameCode}
              onChange={(e) => setGameCode(e.target.value.toUpperCase())}
              placeholder="?????"
              maxLength={4}
              className="w-full px-4 py-3 bg-black/40 border-2 border-haunted-shadow rounded-lg text-haunted-blood text-center text-3xl font-mono placeholder-dark-500 focus:outline-none focus:ring-2 focus:ring-haunted-blood focus:border-haunted-blood transition-all uppercase tracking-widest"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-haunted-fog mb-2">
              Votre nom
            </label>
            <input
              type="text"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleJoinGame()}
              placeholder="Qui ose s'aventurer..."
              className="w-full px-4 py-3 bg-black/40 border-2 border-haunted-shadow rounded-lg text-haunted-fog placeholder-dark-500 focus:outline-none focus:ring-2 focus:ring-haunted-blood focus:border-haunted-blood transition-all"
            />
          </div>

          <button
            onClick={handleJoinGame}
            disabled={loading}
            className="w-full py-3 px-4 bg-haunted-blood hover:bg-red-800 disabled:bg-dark-600 disabled:opacity-50 text-white font-bold rounded-lg transition-all transform hover:scale-105 hover:shadow-[0_0_20px_rgba(139,0,0,0.5)] border border-red-900"
          >
            {loading ? '🕯️ Connexion...' : '🚪 Entrer dans le Manoir'}
          </button>

          <div className="text-center pt-4">
            <button
              onClick={() => navigate('/')}
              className="text-haunted-fog/70 hover:text-haunted-blood underline transition-colors"
            >
              ← Retourner dans les ténèbres
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Join
