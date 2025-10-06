import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { getGameState, startGame, rollDice, makeSuggestion, makeAccusation, passTurn } from '../api'
import InvestigationGrid from '../components/InvestigationGrid'
import GameBoard from '../components/GameBoard'
import AINavigator from '../components/AINavigator'

function Game() {
  const { gameId, playerId } = useParams()
  const [gameState, setGameState] = useState(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  // Suggestion form
  const [selectedSuspect, setSelectedSuspect] = useState('')
  const [selectedWeapon, setSelectedWeapon] = useState('')
  const [selectedRoom, setSelectedRoom] = useState('')
  const [revealedCard, setRevealedCard] = useState(null)
  const [victoryModal, setVictoryModal] = useState(null)

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
      const result = await makeSuggestion(gameId, playerId, selectedSuspect, selectedWeapon, selectedRoom)

      // Show revealed card if any
      if (result.card_shown) {
        setRevealedCard({
          ...result.card_shown,
          disprover: result.disprover
        })
        setTimeout(() => setRevealedCard(null), 5000) // Hide after 5 seconds
      } else {
        alert('Personne ne peut réfuter votre suggestion !')
      }

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
      const result = await makeAccusation(gameId, playerId, selectedSuspect, selectedWeapon, selectedRoom)

      // Show victory modal if correct
      if (result.is_correct && result.solution) {
        setVictoryModal({
          winner: result.winner,
          solution: result.solution,
          victoryComment: result.victory_comment
        })
      }

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

  const me = gameState.players.find(p => p.is_me)
  const isMyTurn = gameState.current_turn?.is_my_turn && me?.is_active
  const canStart = gameState.status === 'waiting' && gameState.players.length >= 3
  const isEliminated = me && !me.is_active

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
                🏰 {gameState.game_name} ({gameState.game_id})
              </h1>
              <p className="text-haunted-fog/80">👤 {me?.name} {!me?.is_active && '💀 (Éliminé)'}</p>
            </div>
            <div className="text-right">
              <p className="text-haunted-fog">
                {gameState.status === 'waiting' ? '⏳ En attente des âmes' :
                 gameState.status === 'in_progress' ? '🎮 Enquête en cours' :
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

        {/* Scenario */}
        {gameState.scenario && gameState.status === 'in_progress' && (
          <div className="bg-black/60 backdrop-blur-md p-6 rounded-lg border-2 border-haunted-purple/30">
            <h2 className="text-xl font-bold text-haunted-purple mb-3 animate-flicker">📜 Le Mystère</h2>
            <p className="text-haunted-fog italic">{gameState.scenario}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Game Board */}
          <div className="lg:col-span-2">
            <GameBoard
              boardLayout={gameState.board_layout}
              players={gameState.players}
              rooms={gameState.rooms}
              myPosition={gameState.my_position}
            />
          </div>

          {/* My Cards */}
          <div className="bg-black/60 backdrop-blur-md p-6 rounded-lg border-2 border-haunted-shadow">
            <h2 className="text-xl font-bold text-haunted-blood mb-4 animate-flicker">🃏 Vos Indices</h2>
            <div className="space-y-2">
              {gameState.my_cards?.map((card, idx) => (
                <div key={idx} className="bg-black/40 px-4 py-2 rounded text-haunted-fog border border-haunted-shadow hover:border-haunted-blood/50 transition-all">
                  {card.type === 'character' && '👤 '}
                  {card.type === 'weapon' && '🔪 '}
                  {card.type === 'room' && '🏚️ '}
                  {card.name}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Investigation Grid */}
        <InvestigationGrid
          suspects={gameState.suspects}
          weapons={gameState.weapons}
          rooms={gameState.rooms}
          myCards={gameState.my_cards}
        />

        {/* AI Narrator */}
        {gameState.use_ai && (
          <AINavigator
            recentActions={gameState.recent_actions}
            gameStatus={gameState.status}
          />
        )}

        {/* Revealed Card Modal */}
        {revealedCard && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in">
            <div className="bg-black/90 border-4 border-haunted-blood p-8 rounded-lg shadow-2xl max-w-md">
              <h3 className="text-2xl font-bold text-haunted-blood mb-4 animate-flicker">🃏 Carte Révélée</h3>
              <p className="text-haunted-fog mb-2">
                <span className="font-semibold">{revealedCard.disprover}</span> vous montre :
              </p>
              <div className="bg-haunted-blood/20 border-2 border-haunted-blood p-4 rounded-lg">
                <p className="text-2xl font-bold text-haunted-fog text-center">
                  {revealedCard.type === 'character' && '👤 '}
                  {revealedCard.type === 'weapon' && '🔪 '}
                  {revealedCard.type === 'room' && '🏚️ '}
                  {revealedCard.name}
                </p>
              </div>
              <p className="text-haunted-fog/60 text-sm mt-4 text-center italic">
                Cette carte disparaîtra dans quelques secondes...
              </p>
            </div>
          </div>
        )}

        {/* Actions */}
        {gameState.status === 'in_progress' && (
          <div className="bg-black/60 backdrop-blur-md p-6 rounded-lg border-2 border-haunted-blood/30">
            <h2 className="text-2xl font-bold text-haunted-blood mb-4 animate-flicker">
              {isEliminated ? '💀 Vous êtes éliminé - Vous pouvez toujours observer' :
               isMyTurn ? '⚡ À vous de jouer !' :
               '⏳ ' + gameState.current_turn?.player_name + ' enquête...'}
            </h2>

            {isMyTurn && !isEliminated && (
              <div className="space-y-4">
                <div className="flex gap-4 mb-4">
                  <button
                    onClick={handleRollDice}
                    disabled={actionLoading || gameState.current_turn.has_rolled}
                    className="px-6 py-3 bg-haunted-blood hover:bg-red-800 disabled:bg-dark-600 disabled:opacity-50 text-white font-bold rounded-lg transition-all hover:shadow-[0_0_20px_rgba(139,0,0,0.5)] border border-red-900"
                  >
                    🎲 {gameState.current_turn.has_rolled ? 'Dés lancés' : 'Lancer les dés'}
                  </button>
                  <button
                    onClick={handlePassTurn}
                    disabled={actionLoading}
                    className="px-6 py-3 bg-black/40 hover:bg-black/60 disabled:opacity-50 text-haunted-fog border-2 border-haunted-shadow font-semibold rounded-lg transition-all"
                  >
                    ⏭️ Passer
                  </button>
                </div>
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
                          {gameState.suspects?.map((s, i) => (
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
                          {gameState.weapons?.map((w, i) => (
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
                          {gameState.rooms?.map((r, i) => (
                            <option key={i} value={r}>{r}</option>
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
                    </div>
                  </div>
              </div>
            )}
          </div>
        )}

        {/* Historique */}
        <div className="bg-black/60 backdrop-blur-md p-6 rounded-lg border-2 border-haunted-shadow">
          <h2 className="text-xl font-bold text-haunted-blood mb-4 animate-flicker">📜 Journal de l'Enquête</h2>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {gameState.recent_actions?.slice().reverse().map((action, idx) => (
              <div key={idx} className="text-haunted-fog/80 text-sm border-l-2 border-haunted-blood pl-3 py-1 hover:bg-black/20 transition-all">
                <span className="font-semibold">{action.player}</span> - {action.action}: {action.details}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Victory Modal */}
      {victoryModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in">
          <div className="bg-gradient-to-b from-haunted-blood to-black p-8 rounded-lg border-4 border-haunted-purple max-w-lg mx-4 animate-bounce-in shadow-[0_0_50px_rgba(139,0,0,0.8)]">
            <div className="text-center">
              <h2 className="text-4xl font-bold text-white mb-4 animate-flicker">
                🎉 Victoire !
              </h2>
              <p className="text-2xl text-haunted-purple mb-6">
                {victoryModal.winner} a résolu l'enquête !
              </p>

              <div className="bg-black/60 p-6 rounded-lg mb-6 border-2 border-haunted-purple/50">
                <h3 className="text-xl font-bold text-haunted-fog mb-4">Solution :</h3>
                <div className="space-y-2 text-lg">
                  <p><span className="text-haunted-purple font-bold">Suspect :</span> {victoryModal.solution.suspect}</p>
                  <p><span className="text-haunted-purple font-bold">Arme :</span> {victoryModal.solution.weapon}</p>
                  <p><span className="text-haunted-purple font-bold">Lieu :</span> {victoryModal.solution.room}</p>
                </div>
              </div>

              {victoryModal.victoryComment && (
                <div className="bg-black/80 p-4 rounded-lg border-l-4 border-haunted-purple mb-6">
                  <p className="text-sm text-haunted-fog/70 mb-1">👻 Desland :</p>
                  <p className="text-haunted-fog italic">"{victoryModal.victoryComment}"</p>
                </div>
              )}

              <div className="flex gap-4 justify-center">
                <button
                  onClick={() => window.location.href = '/'}
                  className="px-6 py-3 bg-haunted-purple hover:bg-purple-800 text-white font-bold rounded-lg transition-all hover:shadow-[0_0_20px_rgba(107,33,168,0.5)] border border-purple-900"
                >
                  🏠 Accueil
                </button>
                <button
                  onClick={() => window.location.reload()}
                  className="px-6 py-3 bg-haunted-blood hover:bg-red-800 text-white font-bold rounded-lg transition-all hover:shadow-[0_0_20px_rgba(139,0,0,0.5)] border border-red-900"
                >
                  🔄 Nouvelle partie
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Game
