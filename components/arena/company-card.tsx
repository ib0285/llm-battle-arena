import type { CSSProperties } from 'react'
import { formatIndex, formatNumber, type Company } from '@/lib/arena-data'
import { BrandLogo } from './brand-logo'
import { TodayDelta } from './today-delta'
import styles from './arena.module.css'

type Box = { left: number; top: number; width: number; height: number }

type CompanyCardProps = {
  company: Company
  box: Box
  splitName?: boolean
  selected?: boolean
  onSelect?: () => void
  /** One-shot orbit into this slot. Off after the intro, or immediately on tap. */
  entering?: boolean
  /** Smooth left/top move when this card changes rank slot. */
  gliding?: boolean
  enterIndex?: number
}

const u = (n: number) => `calc(${n} * var(--u))`

/** Shift that places the card where a rotation around the ring center would. */
function arcShift(box: Box, deg: number) {
  const vx = box.left + box.width / 2 - 380
  const vy = box.top + box.height / 2 - 315
  const a = (deg * Math.PI) / 180
  const rx = vx * Math.cos(a) - vy * Math.sin(a)
  const ry = vx * Math.sin(a) + vy * Math.cos(a)
  return { x: rx - vx, y: ry - vy }
}

export function CompanyCard({
  company,
  box,
  splitName,
  selected,
  onSelect,
  entering,
  gliding,
  enterIndex = 0,
}: CompanyCardProps) {
  const qualified = company.status === 'ok' && company.index !== null
  const scoreText = qualified ? formatIndex(company.index as number) : '—'
  const label = company.status === 'not_enough_posts' ? 'not enough posts' : "This week's score"
  const from = arcShift(box, -84)
  const mid = arcShift(box, -36)
  const style = {
    '--accent': company.accent,
    '--enter-delay': `${enterIndex * 60}ms`,
    '--from-x': from.x,
    '--from-y': from.y,
    '--mid-x': mid.x,
    '--mid-y': mid.y,
    left: u(box.left),
    top: u(box.top),
    width: u(box.width),
    minHeight: u(box.height),
  } as CSSProperties

  const [first, ...rest] = company.name.split(' ')

  const className = [styles.card, selected ? styles.cardOn : '', gliding ? styles.cardGlide : '', entering ? styles.cardEnter : '']
    .filter(Boolean)
    .join(' ')

  return (
    <article
      className={className}
      style={style}
      data-company={company.id}
      role="button"
      tabIndex={0}
      aria-pressed={selected}
      aria-label={`${company.name}: ${qualified ? scoreText : label}. Show posts.`}
      onClick={onSelect}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          onSelect?.()
        }
      }}
    >
      <div className={styles.cardFace}>
      <div className={styles.cardHead}>
        <BrandLogo company={company} className={styles.cardLogo} />
        <h2 className={styles.cardName}>
          {splitName && rest.length ? (
            <>
              {first}
              <br />
              {rest.join(' ')}
            </>
          ) : (
            company.name
          )}
        </h2>
      </div>

      <p className={styles.cardScore}>{scoreText}</p>
      <p className={styles.cardLabel}>{label}</p>
      {qualified ? <TodayDelta value={company.delta} place="card" /> : null}

      <div
        className={styles.bar}
        role="progressbar"
        aria-label={`${company.name} score versus the leader`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(company.progress * 100)}
      >
        <div className={styles.barFill} style={{ width: `${company.progress * 100}%` }} />
      </div>

      <div className={styles.cardFoot}>
        <span>
          {formatNumber(company.posts)} posts · 7d
        </span>
      </div>
      </div>
    </article>
  )
}
