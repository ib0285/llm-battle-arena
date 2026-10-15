import { formatNumber, type Company } from '@/lib/arena-data'
import styles from './arena.module.css'

export function CompanyLogo({ company, className }: { company: Company; className?: string }) {
  if (company.logoMode === 'image') {
    return <img src={company.logo} alt="" className={className ? `${styles.logoImg} ${className}` : styles.logoImg} />
  }

  return (
    <span
      className={className ? `${styles.logoMask} ${className}` : styles.logoMask}
      style={{
        background: company.logoColor || company.accent,
        WebkitMaskImage: `url(${company.logo})`,
        maskImage: `url(${company.logo})`,
      }}
      aria-hidden="true"
    />
  )
}

export function CompanyCard({
  company,
  box,
  splitName = false,
}: {
  company: Company
  box: { left: number; top: number; width: number; height: number }
  splitName?: boolean
}) {
  const [first, ...rest] = company.name.split(' ')
  const progress = Math.max(0, Math.min(1, company.progress))

  return (
    <article
      className={styles.card}
      data-company={company.id}
      data-score={company.score}
      style={{
        left: box.left,
        top: box.top,
        width: box.width,
        height: box.height,
        ['--accent' as string]: company.accent,
      }}
    >
      <div className={styles.cardTop}>
        <CompanyLogo company={company} />
        <div className={styles.cardIdentity}>
          {splitName ? (
            <>
              <p className={styles.cardName}>{first}</p>
              <p className={styles.cardName}>{rest.join(' ')}</p>
            </>
          ) : (
            <p className={styles.cardName}>{company.name}</p>
          )}
          {company.badge ? <p className={styles.badge}>{company.badge}</p> : null}
        </div>
      </div>
      <p className={styles.cardScore}>{formatNumber(company.score)}</p>
      <p className={styles.cardPosts}>{formatNumber(company.posts)} posts</p>
      <div className={styles.track} aria-hidden="true">
        <div className={styles.bar} style={{ width: `${Math.round(progress * 100)}%` }} />
      </div>
    </article>
  )
}
