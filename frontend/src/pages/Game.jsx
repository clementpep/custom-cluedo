import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { getGameState, startGame, rollDice, makeSuggestion, makeAccusation, passTurn } from '../api'

function Game() {
  const { gameId, playerId } = useParams()
  const [gameState, setGameState] = useState(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  // Suggestion form
  const [selectedSuspect, setSelectedSuspect] = useState('')
  const [selectedWeapon, setSelectedWeapon] = useState('')
  const [selectedRoom, setSelectedRoom] = useState('')

  useEffect(() => {
    loadGameState()
    const interval = setInterval(loadGameState, 2000)
    return () => clearInterval(interval)
  }, [gameId, playerId])

  const loadGameState = async () => {
    try {
      const state = await getGameState(gameId, playerId)
      setGameState(state)
      setLoading(false)
    } catch (error) {
      console.error('Erreur chargement:', error)
    }
  }

  const handleStartGame = async () => {
    setActionLoading(true)
    try {
      await startGame(gameId, playerId)
      await loadGameState()
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur au démarrage')
    } finally {
      setActionLoading(false)
    }
  }

  const handleRollDice = async () => {
    setActionLoading(true)
    try {
      await rollDice(gameId, playerId)
      await loadGameState()
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur lors du lancer de dés')
    } finally {
      setActionLoading(false)
    }
  }

  const handleSuggestion = async () => {
    if (!selectedSuspect || !selectedWeapon || !selectedRoom) {
      alert('Sélectionnez tous les éléments')
      return
    }
    setActionLoading(true)
    try {
      await makeSuggestion(gameId, playerId, selectedSuspect, selectedWeapon, selectedRoom)
      await loadGameState()
      setSelectedSuspect('')
      setSelectedWeapon('')
      setSelectedRoom('')
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur lors de la suggestion')
    } finally {
      setActionLoading(false)
    }
  }

  const handleAccusation = async () => {
    if (!selectedSuspect || !selectedWeapon || !selectedRoom) {
      alert('Sélectionnez tous les éléments')
      return
    }
    if (!confirm('⚠️ Une accusation incorrecte vous élimine. Continuer ?')) return

    setActionLoading(true)
    try {
      await makeAccusation(gameId, playerId, selectedSuspect, selectedWeapon, selectedRoom)
      await loadGameState()
      setSelectedSuspect('')
      setSelectedWeapon('')
      setSelectedRoom('')
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur lors de l\'accusation')
    } finally {
      setActionLoading(false)
    }
  }

  const handlePassTurn = async () => {
    setActionLoading(true)
    try {
      await passTurn(gameId, playerId)
      await loadGameState()
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur')
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-haunted-gradient flex items-center justify-center">
        <div className="text-haunted-blood text-2xl animate-flicker">🕯️ Chargement des ténèbres...</div>
      </div>
    )
  }

  const me = gameState.players.find(p => p.id === playerId)
  const isMyTurn = gameState.current_player_id === playerId
  const canStart = me?.is_creator && gameState.status === 'waiting' && gameState.players.length >= 3

  return (
    <div className="min-h-screen bg-haunted-gradient p-4 relative overflow-hidden">
      {/* Animated fog effect */}
      <div className="absolute inset-0 bg-fog-gradient opacity-10 animate-pulse-slow pointer-events-none"></div>

      <div className="max-w-6xl mx-auto space-y-6 relative z-10">
        {/* Header */}
        <div className="bg-black/60 backdrop-blur-md p-6 rounded-lg border-2 border-haunted-blood/30 shadow-[0_0_30px_rgba(139,0,0,0.2)]">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-4xl font-bold text-haunted-blood mb-1 animate-flicker drop-shadow-[0_0_10px_rgba(139,0,0,0.5)]">
                🏰 Manoir {gameState.game_code}
              </h1>
              <p className="text-haunted-fog/80">👤 {me?.name} {me?.is_eliminated && '💀 (Éliminé)'}</p>
            </div>
            <div className="text-right">
              <p className="text-haunted-fog">
                {gameState.status === 'waiting' ? '⏳ En attente des âmes' :
                 gameState.status === 'playing' ? '🎮 Enquête en cours' :
                 '🏆 Mystère résolu'}
              </p>
              <p className="text-haunted-fog/60 text-sm">{gameState.players.length} âmes perdues</p>
            </div>
          </div>
          {canStart && (
            <button
              onClick={handleStartGame}
              disabled={actionLoading}
              className="mt-4 px-6 py-2 bg-haunted-blood hover:bg-red-800 disabled:bg-dark-600 disabled:opacity-50 text-white font-bold rounded-lg transition-all hover:shadow-[0_0_20px_rgba(139,0,0,0.5)] border border-red-900"
            >
              🚀 Commencer l'enquête
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Plateau */}
          <div className="bg-black/60 backdrop-blur-md p-6 rounded-lg border-2 border-haunted-shadow">
            <h2 className="text-xl font-bold text-haunted-blood mb-4 animate-flicker">🏰 Les Pièces du Manoir</h2>
            <div className="space-y-2">
              {gameState.board?.rooms.map((room, idx) => (
                <div key={idx} className="bg-black/40 p-3 rounded border border-haunted-shadow hover:border-haunted-blood/50 transition-all">
                  <div className="font-semibold text-haunted-fog">{room.name}</div>
                  <div className="text-sm text-haunted-fog/60">
                    👥 {room.player_ids.map(id =>
                      gameState.players.find(p => p.id === id)?.name || id
                    ).join(', ') || 'Aucune âme'}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Mes cartes */}
          <div className="bg-black/60 backdrop-blur-md p-6 rounded-lg border-2 border-haunted-shadow">
            <h2 className="text-xl font-bold text-haunted-blood mb-4 animate-flicker">🃏 Vos Indices</h2>
            <div className="space-y-2">
              {me?.cards.map((card, idx) => (
                <div key={idx} className="bg-black/40 px-4 py-2 rounded text-haunted-fog border border-haunted-shadow hover:border-haunted-blood/50 transition-all">
                  {card.type === 'suspect' && '👤 '}
                  {card.type === 'weapon' && '🔪 '}
                  {card.type === 'room' && '🏚️ '}
                  {card.name}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Actions */}
        {gameState.status === 'playing' && (
          <div className="bg-black/60 backdrop-blur-md p-6 rounded-lg border-2 border-haunted-blood/30">
            <h2 className="text-2xl font-bold text-haunted-blood mb-4 animate-flicker">
              {isMyTurn ? '⚡ À vous de jouer !' : '⏳ ' + gameState.players.find(p => p.id === gameState.current_player_id)?.name + ' enquête...'}
            </h2>

            {isMyTurn && (
              <div className="space-y-4">
                {!me.has_moved ? (
                  <div className="flex gap-4">
                    <button
                      onClick={handleRollDice}
                      disabled={actionLoading}
                      className="px-6 py-3 bg-haunted-blood hover:bg-red-800 disabled:bg-dark-600 disabled:opacity-50 text-white font-bold rounded-lg transition-all hover:shadow-[0_0_20px_rgba(139,0,0,0.5)] border border-red-900"
                    >
                      🎲 Lancer les dés
                    </button>
                    <button
                      onClick={handlePassTurn}
                      disabled={actionLoading}
                      className="px-6 py-3 bg-black/40 hover:bg-black/60 disabled:opacity-50 text-haunted-fog border-2 border-haunted-shadow font-semibold rounded-lg transition-all"
                    >
                      ⏭️ Passer
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <label className="block text-sm text-haunted-fog mb-2">👤 Suspect</label>
                        <select
                          value={selectedSuspect}
                          onChange={(e) => setSelectedSuspect(e.target.value)}
                          className="w-full px-3 py-2 bg-black/40 text-haunted-fog rounded border-2 border-haunted-shadow focus:border-haunted-blood focus:outline-none"
                        >
                          <option value="">--</option>
                          {gameState.board?.suspects.map((s, i) => (
                            <option key={i} value={s}>{s}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm text-haunted-fog mb-2">🔪 Arme</label>
                        <select
                          value={selectedWeapon}
                          onChange={(e) => setSelectedWeapon(e.target.value)}
                          className="w-full px-3 py-2 bg-black/40 text-haunted-fog rounded border-2 border-haunted-shadow focus:border-haunted-blood focus:outline-none"
                        >
                          <option value="">--</option>
                          {gameState.board?.weapons.map((w, i) => (
                            <option key={i} value={w}>{w}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm text-haunted-fog mb-2">🏚️ Pièce</label>
                        <select
                          value={selectedRoom}
                          onChange={(e) => setSelectedRoom(e.target.value)}
                          className="w-full px-3 py-2 bg-black/40 text-haunted-fog rounded border-2 border-haunted-shadow focus:border-haunted-blood focus:outline-none"
                        >
                          <option value="">--</option>
                          {gameState.board?.rooms.map((r, i) => (
                            <option key={i} value={r.name}>{r.name}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                    <div className="flex gap-4">
                      <button
                        onClick={handleSuggestion}
                        disabled={actionLoading}
                        className="px-6 py-3 bg-haunted-purple hover:bg-purple-800 disabled:bg-dark-600 disabled:opacity-50 text-white font-bold rounded-lg transition-all hover:shadow-[0_0_20px_rgba(107,33,168,0.5)] border border-purple-900"
                      >
                        💬 Suggérer
                      </button>
                      <button
                        onClick={handleAccusation}
                        disabled={actionLoading}
                        className="px-6 py-3 bg-haunted-blood hover:bg-red-800 disabled:bg-dark-600 disabled:opacity-50 text-white font-bold rounded-lg transition-all hover:shadow-[0_0_20px_rgba(139,0,0,0.5)] border border-red-900"
                      >
                        ⚠️ Accuser
                      </button>
                      <button
                        onClick={handlePassTurn}
                        disabled={actionLoading}
                        className="px-6 py-3 bg-black/40 hover:bg-black/60 disabled:opacity-50 text-haunted-fog border-2 border-haunted-shadow font-semibold rounded-lg transition-all"
                      >
                        ⏭️ Passer
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Historique */}
        <div className="bg-black/60 backdrop-blur-md p-6 rounded-lg border-2 border-haunted-shadow">
          <h2 className="text-xl font-bold text-haunted-blood mb-4 animate-flicker">📜 Journal de l'Enquête</h2>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {gameState.history?.slice(-10).reverse().map((event, idx) => (
              <div key={idx} className="text-haunted-fog/80 text-sm border-l-2 border-haunted-blood pl-3 py-1 hover:bg-black/20 transition-all">
                {event}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Game
