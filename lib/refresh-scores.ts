'use server'

import { updateTag } from 'next/cache'
import { GITHUB_DATA_URL } from '@/lib/arena-data'

export async function refreshScores(): Promise<{ ok: boolean; updatedAt: string | null }> {
  const join = GITHUB_DATA_URL.includes('?') ? '&' : '?'
  try {
    const res = await fetch(`${GITHUB_DATA_URL}${join}t=${Date.now()}`, { cache: 'no-store' })
    if (!res.ok) return { ok: false, updatedAt: null }
    const data: unknown = await res.json()
    const updatedAt =
      data && typeof data === 'object' && 'updatedAt' in data && typeof data.updatedAt === 'string'
        ? data.updatedAt
        : null
    updateTag('scores')
    return { ok: true, updatedAt }
  } catch {
    return { ok: false, updatedAt: null }
  }
}
