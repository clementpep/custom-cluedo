import { useState, useEffect } from 'react'

function InvestigationGrid({ suspects, weapons, rooms, myCards }) {
  const [notes, setNotes] = useState({})

  // Initialize notes from localStorage and set my cards
  useEffect(() => {
    const saved = localStorage.getItem('investigation_notes')
    const initialNotes = saved ? JSON.parse(saved) : {}

    // Initialize all items as 'unknown' if not already set
    const allItems = [
      ...(suspects?.map(s => ({ name: s, type: 'character' })) || []),
      ...(weapons?.map(w => ({ name: w, type: 'weapon' })) || []),
      ...(rooms?.map(r => ({ name: r, type: 'room' })) || [])
    ]

    allItems.forEach(item => {
      const key = `${item.type}:${item.name}`
      // Check if this is one of my cards
      const isMyCard = myCards?.some(card =>
        card.name === item.name && card.type === item.type
      )

      if (isMyCard) {
        // Always mark my cards as 'mine' (locked)
        initialNotes[key] = 'mine'
      } else if (!(key in initialNotes)) {
        // Only set to unknown if not already tracked
        initialNotes[key] = 'unknown'
      }
    })

    setNotes(initialNotes)
  }, [suspects, weapons, rooms, myCards])

  // Save notes to localStorage
  useEffect(() => {
    localStorage.setItem('investigation_notes', JSON.stringify(notes))
  }, [notes])

  const toggleNote = (item, type) => {
    // Check if this is one of my cards - if so, don't allow toggling
    const isMyCard = myCards?.some(card =>
      card.name === item && card.type === type
    )

    if (isMyCard) {
      return // Can't change status of my own cards
    }

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

  const getButtonClasses = (item, type) => {
    const isMyCard = myCards?.some(card =>
      card.name === item && card.type === type
    )

    const baseClasses = "flex items-center gap-2 px-3 py-2 rounded text-left text-sm border transition-all"

    if (isMyCard) {
      // Grayed out and locked for my cards
      return `${baseClasses} bg-haunted-purple/20 text-haunted-fog/50 border-haunted-purple/40 cursor-not-allowed opacity-70`
    }

    // Normal interactive style for other cards
    return `${baseClasses} bg-black/40 text-haunted-fog border-haunted-shadow hover:border-haunted-blood/50`
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
                className={getButtonClasses(suspect, 'character')}
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
                className={getButtonClasses(weapon, 'weapon')}
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
                className={getButtonClasses(room, 'room')}
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
