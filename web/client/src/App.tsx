import { Route, Routes } from 'react-router-dom'

import { GameDetailPage } from '@/routes/GameDetailPage'
import { LibraryPage } from '@/routes/LibraryPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<LibraryPage />} />
      <Route path="/games/:id" element={<GameDetailPage />} />
      <Route path="*" element={<LibraryPage />} />
    </Routes>
  )
}

export default App
