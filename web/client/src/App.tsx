import { Route, Routes } from 'react-router-dom'

import { GameDetailPage } from '@/routes/GameDetailPage'
import { AccountPage } from '@/routes/AccountPage'
import { ImportPage } from '@/routes/ImportPage'
import { LibraryPage } from '@/routes/LibraryPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<LibraryPage />} />
      <Route path="/games/:id" element={<GameDetailPage />} />
      <Route path="/account" element={<AccountPage />} />
      <Route path="/import" element={<ImportPage />} />
      <Route path="*" element={<LibraryPage />} />
    </Routes>
  )
}

export default App
