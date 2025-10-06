import { useState, useEffect, useRef } from 'react'

function AINavigator({ recentActions, gameStatus }) {
  const [comments, setComments] = useState([])
  const scrollRef = useRef(null)

  useEffect(() => {
    // Extract AI comments from recent actions
    if (recentActions) {
      console.log('[AINavigator] Recent actions:', recentActions)
      const aiComments = recentActions
        .filter(action => {
          const hasComment = !!action.ai_comment
          console.log(`[AINavigator] Action ${action.action} by ${action.player}: has_comment=${hasComment}, comment="${action.ai_comment}"`)
          return hasComment
        })
        .map(action => ({
          id: `${action.player}-${action.action}-${Date.now()}`,
          text: action.ai_comment,
          player: action.player,
          action: action.action
        }))

      console.log('[AINavigator] AI comments found:', aiComments.length)
      setComments(aiComments)
    }
  }, [recentActions])

  useEffect(() => {
    // Auto-scroll to latest comment
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [comments])

  if (gameStatus === 'waiting') {
    return (
      <div className="bg-black/60 backdrop-blur-md p-6 rounded-lg border-2 border-haunted-purple/30">
        <h2 className="text-xl font-bold text-haunted-purple mb-4 animate-flicker">
          👻 Desland, le Narrateur
        </h2>
        <div className="text-haunted-fog/70 italic">
          <p className="mb-2">
            "Je suis Leland... euh non, Desland. Le vieux jardinier de ce manoir maudit."
          </p>
          <p>
            En attendant que les enquêteurs arrivent... s'ils osent.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-black/60 backdrop-blur-md p-6 rounded-lg border-2 border-haunted-purple/30">
      <h2 className="text-xl font-bold text-haunted-purple mb-4 animate-flicker flex items-center gap-2">
        👻 Desland, le Narrateur
        <span className="text-xs text-haunted-fog/60 font-normal">(IA activée)</span>
      </h2>

      <div
        ref={scrollRef}
        className="space-y-3 max-h-64 overflow-y-auto scrollbar-thin scrollbar-thumb-haunted-purple/50 scrollbar-track-black/20"
      >
        {comments.length === 0 ? (
          <div className="text-haunted-fog/60 italic text-sm">
            <p>"Alors, on attend quoi pour commencer cette enquête ridicule ?"</p>
          </div>
        ) : (
          comments.map((comment, idx) => (
            <div
              key={idx}
              className="bg-black/40 p-3 rounded border-l-4 border-haunted-purple animate-fade-in"
            >
              <div className="text-xs text-haunted-fog/50 mb-1">
                {comment.player} • {comment.action}
              </div>
              <div className="text-haunted-fog italic">
                "{comment.text}"
              </div>
            </div>
          ))
        )}
      </div>

      <div className="mt-4 pt-4 border-t border-haunted-shadow text-xs text-haunted-fog/60">
        <p className="italic">
          💀 Desland commente vos actions avec son sarcasme légendaire...
        </p>
      </div>
    </div>
  )
}

export default AINavigator
