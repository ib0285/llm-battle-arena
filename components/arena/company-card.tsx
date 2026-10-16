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
}

const u = (n: number) => `calc(${n} * var(--u))`

export function CompanyCard({ company, box, splitName }: CompanyCardProps) {
  const qualified = company.status === 'ok' && company.index !== null
  const scoreText = qualified ? formatIndex(company.index as number) : '—'
  const label = company.status === 'not_enough_posts' ? 'not enough posts' : 'score · 7d'
  const style = {
    '--accent': company.accent,
    left: u(box.left),
    top: u(box.top),
    width: u(box.width),
    minHeight: u(box.height),
  } as CSSProperties

  const [first, ...rest] = company.name.split(' ')

  return (
    <article className={styles.card} style={style} aria-label={`${company.name}: ${qualified ? scoreText : label}`}>
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
    </article>
  )
}
