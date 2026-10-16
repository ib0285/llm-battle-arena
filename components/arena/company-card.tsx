import type { CSSProperties } from 'react'
import { type Company, formatNumber } from '@/lib/arena-data'
import { BrandLogo } from './brand-logo'
import styles from './arena.module.css'

type Box = { left: number; top: number; width: number; height: number }

type CompanyCardProps = {
  company: Company
  box: Box
  splitName?: boolean
}

const u = (n: number) => `calc(${n} * var(--u))`

export function CompanyCard({ company, box, splitName }: CompanyCardProps) {
  const style = {
    '--accent': company.accent,
    left: u(box.left),
    top: u(box.top),
    width: u(box.width),
    minHeight: u(box.height),
  } as CSSProperties

  const [first, ...rest] = company.name.split(' ')

  return (
    <article className={styles.card} style={style} aria-label={`${company.name}: ${formatNumber(company.score)} engagement`}>
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
        {company.badge && <span className={styles.badge}>{company.badge}</span>}
      </div>

      <p className={styles.cardScore}>{formatNumber(company.score)}</p>
      <p className={styles.cardLabel}>24h Engagement</p>

      <div
        className={styles.bar}
        role="progressbar"
        aria-label={`${company.name} engagement share`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(company.progress * 100)}
      >
        <div className={styles.barFill} style={{ width: `${company.progress * 100}%` }} />
      </div>

      <div className={styles.cardFoot}>
        <span>{formatNumber(company.posts)} posts</span>
      </div>
    </article>
  )
}
