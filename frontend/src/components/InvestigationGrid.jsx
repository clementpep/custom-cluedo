import { useState, useEffect } from 'react'

function InvestigationGrid({ suspects, weapons, rooms, myCards }) {
  const [notes, setNotes] = useState({})

  // Initialize notes from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('investigation_notes')
    if (saved) {
      setNotes(JSON.parse(saved))
    }
  }, [])

  // Save notes to localStorage
  useEffect(() => {
    localStorage.setItem('investigation_notes', JSON.stringify(notes))
  }, [notes])

  const toggleNote = (item, type) => {
    const key = `${type}:${item}`
    setNotes(prev => {
      const current = prev[key] || 'unknown'
      const next = current === 'unknown' ? 'eliminated' :
                   current === 'eliminated' ? 'maybe' : 'unknown'
      return { ...prev, [key]: next }
    })
  }

  const getStatus = (item, type) => {
    const key = `${type}:${item}`
    return notes[key] || 'unknown'
  }

  const getIcon = (item, type) => {
    // Check if this is one of my cards
    const isMyCard = myCards?.some(card =>
      card.name === item && card.type === type
    )

    if (isMyCard) return '✅' // I have this card

    const status = getStatus(item, type)
    if (status === 'eliminated') return '❌'
    if (status === 'maybe') return '❓'
    return '⬜'
  }

  return (
    <div className="bg-black/60 backdrop-blur-md p-6 rounded-lg border-2 border-haunted-shadow">
      <h2 className="text-xl font-bold text-haunted-blood mb-4 animate-flicker">📋 Grille d'Enquête</h2>

      <div className="space-y-4">
        {/* Suspects */}
        <div>
          <h3 className="text-sm font-semibold text-haunted-fog mb-2">👤 SUSPECTS</h3>
          <div className="grid grid-cols-2 gap-2">
            {suspects?.map((suspect, i) => (
              <button
                key={i}
                onClick={() => toggleNote(suspect, 'character')}
                className="flex items-center gap-2 bg-black/40 px-3 py-2 rounded text-left text-sm text-haunted-fog border border-haunted-shadow hover:border-haunted-blood/50 transition-all"
              >
                <span className="text-lg">{getIcon(suspect, 'character')}</span>
                <span className="flex-1 truncate">{suspect}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Weapons */}
        <div>
          <h3 className="text-sm font-semibold text-haunted-fog mb-2">🔪 ARMES</h3>
          <div className="grid grid-cols-2 gap-2">
            {weapons?.map((weapon, i) => (
              <button
                key={i}
                onClick={() => toggleNote(weapon, 'weapon')}
                className="flex items-center gap-2 bg-black/40 px-3 py-2 rounded text-left text-sm text-haunted-fog border border-haunted-shadow hover:border-haunted-blood/50 transition-all"
              >
                <span className="text-lg">{getIcon(weapon, 'weapon')}</span>
                <span className="flex-1 truncate">{weapon}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Rooms */}
        <div>
          <h3 className="text-sm font-semibold text-haunted-fog mb-2">🏚️ SALLES</h3>
          <div className="grid grid-cols-2 gap-2">
            {rooms?.map((room, i) => (
              <button
                key={i}
                onClick={() => toggleNote(room, 'room')}
                className="flex items-center gap-2 bg-black/40 px-3 py-2 rounded text-left text-sm text-haunted-fog border border-haunted-shadow hover:border-haunted-blood/50 transition-all"
              >
                <span className="text-lg">{getIcon(room, 'room')}</span>
                <span className="flex-1 truncate">{room}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-haunted-shadow text-xs text-haunted-fog/60 space-y-1">
        <p>✅ Mes cartes • ❌ Éliminé • ❓ Peut-être • ⬜ Inconnu</p>
        <p className="italic">Cliquez pour changer le statut</p>
      </div>
    </div>
  )
}

export default InvestigationGrid
