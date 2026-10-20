import { ArrowLeft } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'

import { GameDetail } from '@/components/GameDetail'

export function GameDetailPage() {
  const { id } = useParams()

  return (
    <main className="mx-auto max-w-3xl p-4 sm:p-6">
      <Link to="/" className="mb-4 inline-flex items-center gap-1 text-sm text-neutral-400 hover:text-white">
        <ArrowLeft className="size-4" /> Library
      </Link>
      <GameDetail id={Number(id)} />
    </main>
  )
}
