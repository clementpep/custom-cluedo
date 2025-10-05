import { useState } from 'react'

function GameBoard({ boardLayout, players, rooms, myPosition }) {
  if (!boardLayout || !boardLayout.rooms) {
    return (
      <div className="bg-black/60 backdrop-blur-md p-6 rounded-lg border-2 border-haunted-shadow">
        <h2 className="text-xl font-bold text-haunted-blood mb-4 animate-flicker">🏰 Plateau de Jeu</h2>
        <p className="text-haunted-fog/60">Plateau en cours de chargement...</p>
      </div>
    )
  }

  const gridWidth = boardLayout.grid_width || 8
  const gridHeight = boardLayout.grid_height || 8

  // Get players in each room
  const getPlayersInRoom = (roomName) => {
    return players?.filter(p => {
      const roomIndex = rooms?.indexOf(roomName)
      return roomIndex !== -1 && p.position === roomIndex
    }) || []
  }

  return (
    <div className="bg-black/60 backdrop-blur-md p-6 rounded-lg border-2 border-haunted-shadow">
      <h2 className="text-xl font-bold text-haunted-blood mb-4 animate-flicker">🏰 Plateau du Manoir</h2>

      <div
        className="grid gap-2 mx-auto"
        style={{
          gridTemplateColumns: `repeat(${gridWidth}, minmax(0, 1fr))`,
          maxWidth: `${gridWidth * 100}px`
        }}
      >
        {Array.from({ length: gridHeight }).map((_, y) =>
          Array.from({ length: gridWidth }).map((_, x) => {
            const room = boardLayout.rooms.find(r => r.x === x && r.y === y)
            const playersHere = room ? getPlayersInRoom(room.name) : []
            const isMyLocation = room && rooms?.indexOf(room.name) === myPosition

            return (
              <div
                key={`${x}-${y}`}
                className={`
                  aspect-square rounded-lg border-2 transition-all
                  ${room
                    ? isMyLocation
                      ? 'bg-haunted-blood/20 border-haunted-blood shadow-[0_0_20px_rgba(139,0,0,0.3)]'
                      : 'bg-black/40 border-haunted-shadow hover:border-haunted-purple/50'
                    : 'bg-dark-800/20 border-dark-700'
                  }
                `}
              >
                {room ? (
                  <div className="h-full flex flex-col items-center justify-center p-1 text-center">
                    <div className="text-xs font-semibold text-haunted-fog mb-1 truncate w-full">
                      {room.name}
                    </div>
                    {playersHere.length > 0 && (
                      <div className="flex flex-wrap gap-1 justify-center">
                        {playersHere.map((p, i) => (
                          <div
                            key={i}
                            className={`
                              w-6 h-6 rounded-full flex items-center justify-center text-xs
                              ${p.is_me
                                ? 'bg-haunted-blood text-white font-bold'
                                : 'bg-haunted-purple/70 text-white'
                              }
                            `}
                            title={p.name}
                          >
                            {p.name.charAt(0).toUpperCase()}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ) : null}
              </div>
            )
          })
        )}
      </div>

      <div className="mt-4 pt-4 border-t border-haunted-shadow text-xs text-haunted-fog/60">
        <p>🔴 Votre position • 🟣 Autres joueurs</p>
      </div>
    </div>
  )
}

export default GameBoard
