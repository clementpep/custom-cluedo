import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Join from './pages/Join'
import Game from './pages/Game'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gradient-to-br from-dark-950 via-dark-900 to-dark-950">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/join" element={<Join />} />
          <Route path="/game/:gameId/:playerId" element={<Game />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App
