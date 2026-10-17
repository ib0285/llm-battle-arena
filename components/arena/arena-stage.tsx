'use client'

import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { Crown } from 'lucide-react'
import { formatIndex, type Company, type CompanyId } from '@/lib/arena-data'
import { ArenaRings } from './arena-rings'
import { CompanyCard } from './company-card'
import { TodayDelta } from './today-delta'
import styles from './arena.module.css'

const layout: Record<CompanyId, { left: number; top: number; width: number; height: number }> = {
  xai: { left: 265, top: 8, width: 236, height: 156 },
  openai: { left: 17, top: 168, width: 172, height: 158 },
  meta: { left: 565, top: 170, width: 167, height: 158 },
  anthropic: { left: 64, top: 420, width: 172, height: 158 },
  deepmind: { left: 498, top: 422, width: 178, height: 164 },
}

/** Rank 1 sits in the top slot, then clockwise around the ring. */
const slots = [layout.xai, layout.meta, layout.deepmind, layout.anthropic, layout.openai]

const ORDER_KEY = 'arena-ring-order'

/** Survives Companies/Leaders tab switches so the intro does not replay. */
let introPlayedThisLoad = false

function rankIds(companies: Company[]): CompanyId[] {
  return [...companies]
    .sort((a, b) => {
      const aq = a.status === 'ok' && a.index !== null
      const bq = b.status === 'ok' && b.index !== null
      if (aq !== bq) return aq ? -1 : 1
      if (aq && bq) {
        if (b.score !== a.score) return b.score - a.score
        if (b.posts !== a.posts) return b.posts - a.posts
      }
      return a.name.localeCompare(b.name)
    })
    .map((company) => company.id)
}

function sameOrder(a: CompanyId[], b: CompanyId[]) {
  return a.length === b.length && a.every((id, index) => id === b[index])
}

function readOrder(valid: CompanyId[]): CompanyId[] | null {
  try {
    const raw = JSON.parse(localStorage.getItem(ORDER_KEY) || 'null')
    if (!Array.isArray(raw)) return null
    const ids = raw.filter((id): id is CompanyId => valid.includes(id as CompanyId))
    if (ids.length !== valid.length || new Set(ids).size !== valid.length) return null
    return ids
  } catch {
    return null
  }
}

function writeOrder(ids: CompanyId[]) {
  try {
    localStorage.setItem(ORDER_KEY, JSON.stringify(ids))
  } catch {
    /* private mode or a full store */
  }
}

function prefersReducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

export function ArenaStage({
  companies,
  selectedId,
  onSelect,
}: {
  companies: Company[]
  selectedId: string | null
  onSelect: (id: Company['id']) => void
}) {
  const liveOrder = rankIds(companies)
  const liveKey = liveOrder.join(',')
  const [visualOrder, setVisualOrder] = useState(liveOrder)
  const [gliding, setGliding] = useState(false)
  const [intro, setIntro] = useState(false)
  const [pulse, setPulse] = useState(false)
  const booted = useRef(false)
  const shown = useRef(liveOrder)
  const liveRef = useRef(liveOrder)
  const introOn = useRef(false)
  const glideOn = useRef(false)
  const skipClick = useRef(false)
  liveRef.current = liveOrder
  const byId = new Map(companies.map((company) => [company.id, company]))

  const leaderId = liveOrder.find((id) => {
    const company = byId.get(id)
    return company?.status === 'ok' && company.index !== null
  })
  const leader = leaderId ? byId.get(leaderId) : undefined

  useLayoutEffect(() => {
    const live = liveRef.current
    const reduced = prefersReducedMotion()
    const previous = booted.current ? shown.current : (readOrder(live) ?? live)
    const moved = !sameOrder(previous, live)
    const leaderChanged = previous[0] !== live[0]

    if (moved && !reduced) {
      introPlayedThisLoad = true
      introOn.current = false
      setIntro(false)
      setGliding(false)
      setVisualOrder(previous)
      let cancelled = false
      let inner = 0
      let settle = 0
      const outer = requestAnimationFrame(() => {
        inner = requestAnimationFrame(() => {
          if (cancelled) return
          booted.current = true
          shown.current = live
          glideOn.current = true
          setGliding(true)
          setVisualOrder(live)
          writeOrder(live)
          if (leaderChanged) setPulse(true)
          settle = window.setTimeout(() => {
            glideOn.current = false
            setGliding(false)
          }, 800)
        })
      })
      return () => {
        cancelled = true
        cancelAnimationFrame(outer)
        cancelAnimationFrame(inner)
        window.clearTimeout(settle)
      }
    }

    booted.current = true
    shown.current = live
    setGliding(false)
    setVisualOrder(live)
    if (!introPlayedThisLoad && !reduced) {
      introPlayedThisLoad = true
      introOn.current = true
      setIntro(true)
    }
    writeOrder(live)
  }, [liveKey])

  useEffect(() => {
    if (!intro) return
    const timer = window.setTimeout(() => {
      introOn.current = false
      setIntro(false)
    }, 2200)
    return () => window.clearTimeout(timer)
  }, [intro])

  useEffect(() => {
    if (!pulse) return
    const timer = window.setTimeout(() => setPulse(false), 900)
    return () => window.clearTimeout(timer)
  }, [pulse])

  function stopIntro() {
    if (!introOn.current) return
    introOn.current = false
    introPlayedThisLoad = true
    setIntro(false)
  }

  return (
    <section
      className={styles.stage}
      aria-label="Engagement leaderboard"
      data-intro={intro ? 'run' : 'done'}
      data-gliding={gliding ? 'run' : 'off'}
      onPointerDown={(event) => {
        const card = (event.target as HTMLElement).closest('[data-company]')
        const id = card?.getAttribute('data-company')
        if (introOn.current) {
          stopIntro()
          if (id) {
            skipClick.current = true
            onSelect(id as Company['id'])
            window.setTimeout(() => {
              skipClick.current = false
            }, 400)
          }
          return
        }
        if (glideOn.current) {
          glideOn.current = false
          setGliding(false)
          setVisualOrder(liveRef.current)
        }
      }}
    >
      <div className={styles.inner}>
        <ArenaRings />

        <div className={pulse ? `${styles.core} ${styles.corePulse}` : styles.core}>
          {leader ? (
            <>
              <p className={styles.coreLabel}>Current Leader</p>
              <p className={styles.coreName}>
                <span className={styles.goldText}>{leader.name}</span>
                <Crown className={styles.crown} strokeWidth={1.5} aria-hidden="true" />
              </p>
              <p className={styles.coreSub}>Leading the arena</p>
              <p className={`${styles.coreScore} ${styles.goldText}`}>{formatIndex(leader.index as number)}</p>
              <p className={styles.coreUnit}>score · 7d</p>
              <TodayDelta value={leader.delta} place="core" />
            </>
          ) : (
            <>
              <p className={styles.coreLabel}>Current Leader</p>
              <p className={styles.coreSub}>Waiting for 7-day scores</p>
            </>
          )}
        </div>

        {visualOrder.map((id, index) => {
          const company = byId.get(id)
          const box = slots[index]
          if (!company || !box) return null
          return (
            <CompanyCard
              key={company.id}
              company={company}
              box={box}
              splitName={company.id === 'deepmind'}
              selected={selectedId === company.id}
              entering={intro}
              gliding={gliding}
              enterIndex={index}
              onSelect={() => {
                if (skipClick.current) {
                  skipClick.current = false
                  return
                }
                onSelect(company.id)
              }}
            />
          )
        })}
      </div>
    </section>
  )
}
