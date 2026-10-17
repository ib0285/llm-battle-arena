'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { RotateCw } from 'lucide-react'
import { formatUpdated } from '@/lib/arena-data'
import { refreshScores } from '@/lib/refresh-scores'
import styles from './arena.module.css'

export function UpdatedLabel({ updatedAt }: { updatedAt: string | null }) {
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    const tick = () => setNow(Date.now())
    window.addEventListener('arena:scores-refreshed', tick)
    return () => window.removeEventListener('arena:scores-refreshed', tick)
  }, [])

  const label = formatUpdated(updatedAt, now)
  if (!label) return null
  return <span className={styles.updating}>{label}</span>
}

export function RefreshScores({ updatedAt }: { updatedAt: string | null }) {
  const router = useRouter()
  const [busy, setBusy] = useState(false)
  const [note, setNote] = useState<string | null>(null)

  useEffect(() => {
    if (!note || note === 'Updating…') return
    const timer = window.setTimeout(() => setNote(null), 2500)
    return () => window.clearTimeout(timer)
  }, [note])

  async function refresh() {
    if (busy) return
    setBusy(true)
    setNote('Updating…')
    try {
      const body = await refreshScores()
      window.dispatchEvent(new Event('arena:scores-refreshed'))
      if (!body.ok) {
        setNote("Couldn't refresh")
        return
      }
      const next = body.updatedAt
      if (next && next === updatedAt) {
        setNote('Already up to date')
        return
      }
      setNote('Updated')
      await router.refresh()
    } catch {
      setNote("Couldn't refresh")
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className={styles.refreshWrap}>
      {note ? (
        <p className={styles.refreshNote} role="status">
          {note}
        </p>
      ) : null}
      <button
        type="button"
        className={styles.refresh}
        aria-label="Refresh scores"
        aria-busy={busy}
        onClick={() => void refresh()}
      >
        <RotateCw className={busy ? `${styles.refreshIcon} ${styles.refreshSpin}` : styles.refreshIcon} aria-hidden="true" />
      </button>
    </div>
  )
}
