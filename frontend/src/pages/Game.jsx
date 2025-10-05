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
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-accent-400 text-xl">Chargement...</div>
      </div>
    )
  }

  const me = gameState.players.find(p => p.id === playerId)
  const isMyTurn = gameState.current_player_id === playerId
  const canStart = me?.is_creator && gameState.status === 'waiting' && gameState.players.length >= 3

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-dark-800 p-6 rounded-lg border border-dark-700">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-accent-400">🔍 Partie {gameState.game_code}</h1>
              <p className="text-dark-300">Joueur: {me?.name}</p>
            </div>
            <div className="text-right">
              <p className="text-dark-300">Status: {gameState.status === 'waiting' ? '⏳ En attente' : gameState.status === 'playing' ? '🎮 En cours' : '🏆 Terminée'}</p>
              <p className="text-dark-400 text-sm">{gameState.players.length} joueurs</p>
            </div>
          </div>
          {canStart && (
            <button
              onClick={handleStartGame}
              disabled={actionLoading}
              className="mt-4 px-6 py-2 bg-green-600 hover:bg-green-700 disabled:bg-dark-600 text-white font-semibold rounded-lg"
            >
              🚀 Démarrer la partie
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Plateau */}
          <div className="bg-dark-800 p-6 rounded-lg border border-dark-700">
            <h2 className="text-xl font-bold text-accent-400 mb-4">🏰 Plateau</h2>
            <div className="space-y-2">
              {gameState.board?.rooms.map((room, idx) => (
                <div key={idx} className="bg-dark-700 p-3 rounded">
                  <div className="font-semibold text-white">{room.name}</div>
                  <div className="text-sm text-dark-300">
                    Joueurs: {room.player_ids.map(id =>
                      gameState.players.find(p => p.id === id)?.name || id
                    ).join(', ') || 'Aucun'}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Mes cartes */}
          <div className="bg-dark-800 p-6 rounded-lg border border-dark-700">
            <h2 className="text-xl font-bold text-accent-400 mb-4">🃏 Mes cartes</h2>
            <div className="space-y-2">
              {me?.cards.map((card, idx) => (
                <div key={idx} className="bg-dark-700 px-4 py-2 rounded text-white">
                  {card.type === 'suspect' && '👤 '}
                  {card.type === 'weapon' && '🔪 '}
                  {card.type === 'room' && '🏠 '}
                  {card.name}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Actions */}
        {gameState.status === 'playing' && (
          <div className="bg-dark-800 p-6 rounded-lg border border-dark-700">
            <h2 className="text-xl font-bold text-accent-400 mb-4">
              {isMyTurn ? '⚡ À votre tour !' : '⏳ Tour de ' + gameState.players.find(p => p.id === gameState.current_player_id)?.name}
            </h2>

            {isMyTurn && (
              <div className="space-y-4">
                {!me.has_moved ? (
                  <div className="flex gap-4">
                    <button
                      onClick={handleRollDice}
                      disabled={actionLoading}
                      className="px-6 py-3 bg-accent-600 hover:bg-accent-700 disabled:bg-dark-600 text-white font-semibold rounded-lg"
                    >
                      🎲 Lancer les dés
                    </button>
                    <button
                      onClick={handlePassTurn}
                      disabled={actionLoading}
                      className="px-6 py-3 bg-dark-600 hover:bg-dark-500 text-white font-semibold rounded-lg"
                    >
                      ⏭️ Passer
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <label className="block text-sm text-dark-300 mb-2">Suspect</label>
                        <select
                          value={selectedSuspect}
                          onChange={(e) => setSelectedSuspect(e.target.value)}
                          className="w-full px-3 py-2 bg-dark-700 text-white rounded border border-dark-600"
                        >
                          <option value="">--</option>
                          {gameState.board?.suspects.map((s, i) => (
                            <option key={i} value={s}>{s}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm text-dark-300 mb-2">Arme</label>
                        <select
                          value={selectedWeapon}
                          onChange={(e) => setSelectedWeapon(e.target.value)}
                          className="w-full px-3 py-2 bg-dark-700 text-white rounded border border-dark-600"
                        >
                          <option value="">--</option>
                          {gameState.board?.weapons.map((w, i) => (
                            <option key={i} value={w}>{w}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm text-dark-300 mb-2">Pièce</label>
                        <select
                          value={selectedRoom}
                          onChange={(e) => setSelectedRoom(e.target.value)}
                          className="w-full px-3 py-2 bg-dark-700 text-white rounded border border-dark-600"
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
                        className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-dark-600 text-white font-semibold rounded-lg"
                      >
                        💬 Suggérer
                      </button>
                      <button
                        onClick={handleAccusation}
                        disabled={actionLoading}
                        className="px-6 py-3 bg-red-600 hover:bg-red-700 disabled:bg-dark-600 text-white font-semibold rounded-lg"
                      >
                        ⚠️ Accuser
                      </button>
                      <button
                        onClick={handlePassTurn}
                        disabled={actionLoading}
                        className="px-6 py-3 bg-dark-600 hover:bg-dark-500 text-white font-semibold rounded-lg"
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
        <div className="bg-dark-800 p-6 rounded-lg border border-dark-700">
          <h2 className="text-xl font-bold text-accent-400 mb-4">📜 Historique</h2>
          <div className="space-y-2">
            {gameState.history?.slice(-10).reverse().map((event, idx) => (
              <div key={idx} className="text-dark-300 text-sm border-l-2 border-accent-600 pl-3 py-1">
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
