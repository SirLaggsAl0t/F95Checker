import { useQuery } from '@tanstack/react-query'
import { useEffect } from 'react'
import { Route, Routes } from 'react-router-dom'

import { apiGet } from '@/api/client'
import type { Settings } from '@/api/types'
import { applyTheme } from '@/lib/theme'
import { AccountPage } from '@/routes/AccountPage'
import { GameDetailPage } from '@/routes/GameDetailPage'
import { ImportPage } from '@/routes/ImportPage'
import { LibraryPage } from '@/routes/LibraryPage'
import { SettingsPage } from '@/routes/SettingsPage'
import { TimelinePage } from '@/routes/TimelinePage'

function App() {
  // One settings query for the whole app; pages reuse the cache.
  const settings = useQuery({ queryKey: ['settings'], queryFn: () => apiGet<Settings>('/api/settings') })

  useEffect(() => {
    if (settings.data) applyTheme(settings.data)
  }, [settings.data])

  return (
    <Routes>
      <Route path="/" element={<LibraryPage />} />
      <Route path="/games/:id" element={<GameDetailPage />} />
      <Route path="/account" element={<AccountPage />} />
      <Route path="/import" element={<ImportPage />} />
      <Route path="/settings" element={<SettingsPage />} />
      <Route path="/timeline" element={<TimelinePage />} />
      <Route path="*" element={<LibraryPage />} />
    </Routes>
  )
}

export default App
