import { ImageResponse } from 'next/og'
import { fetchArenaData, formatIndex } from '@/lib/arena-data'

export const alt = 'LLM Battle Arena leaderboard'
export const size = { width: 1200, height: 630 }
export const contentType = 'image/png'
export const revalidate = 300

export default async function OpenGraphImage() {
  const { companies } = await fetchArenaData()
  const rows = [...companies].sort((a, b) => {
    const rank = (status: string) => (status === 'ok' ? 1 : 0)
    if (rank(a.status) !== rank(b.status)) return rank(b.status) - rank(a.status)
    return b.score - a.score
  })

  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          background: '#07070b',
          color: '#ffffff',
          padding: '52px 64px',
        }}
      >
        <div style={{ display: 'flex', fontSize: 22, letterSpacing: 3, color: '#3ee07a', fontWeight: 700 }}>
          LLM BATTLE ARENA
        </div>
        <div style={{ display: 'flex', fontSize: 52, fontWeight: 700, marginTop: 16, letterSpacing: -1 }}>
          Who&apos;s winning attention on X
        </div>
        <div style={{ display: 'flex', fontSize: 26, color: '#b6b4c2', marginTop: 10 }}>
          Companies · engagement per follower, rolling 7 days
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', marginTop: 36 }}>
          {rows.map((company) => {
            const label =
              company.status === 'ok' && company.index !== null
                ? formatIndex(company.index)
                : company.status === 'not_enough_posts'
                  ? 'not enough posts'
                  : '—'
            return (
              <div
                key={company.id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  borderTop: '1px solid rgba(255,255,255,0.12)',
                  padding: '14px 0',
                  fontSize: 34,
                }}
              >
                <div style={{ display: 'flex' }}>{company.name}</div>
                <div style={{ display: 'flex', color: company.status === 'ok' ? '#ffffff' : '#b6b4c2' }}>{label}</div>
              </div>
            )
          })}
        </div>
      </div>
    ),
    { ...size },
  )
}
