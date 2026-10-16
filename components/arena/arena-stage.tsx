import { Crown } from 'lucide-react'
import { formatNumber, type Company, type CompanyId } from '@/lib/arena-data'
import { ArenaRings } from './arena-rings'
import { CompanyCard } from './company-card'
import styles from './arena.module.css'

const layout: Record<CompanyId, { left: number; top: number; width: number; height: number }> = {
  xai: { left: 265, top: 8, width: 236, height: 156 },
  openai: { left: 17, top: 168, width: 172, height: 158 },
  meta: { left: 565, top: 170, width: 167, height: 158 },
  anthropic: { left: 64, top: 420, width: 172, height: 158 },
  deepmind: { left: 498, top: 422, width: 178, height: 164 },
}

export function ArenaStage({ companies }: { companies: Company[] }) {
  const leader = [...companies].sort((a, b) => b.score - a.score)[0]

  if (!leader) {
    return (
      <section className={styles.stage} aria-label="Engagement leaderboard">
        <p className={styles.empty}>Scores aren’t available right now. Please check back in a few minutes.</p>
      </section>
    )
  }

  return (
    <section className={styles.stage} aria-label="Engagement leaderboard">
      <div className={styles.inner}>
        <ArenaRings />

        <div className={styles.core}>
          <p className={styles.coreLabel}>Current Leader</p>
          <p className={styles.coreName}>
            <span className={styles.goldText}>{leader.name}</span>
            <Crown className={styles.crown} strokeWidth={1.5} aria-hidden="true" />
          </p>
          <p className={styles.coreSub}>Leading the arena</p>
          <p className={`${styles.coreScore} ${styles.goldText}`}>{formatNumber(leader.score)}</p>
          <p className={styles.coreUnit}>Avg per post</p>
        </div>

        {companies.map((c) => (
          <CompanyCard key={c.id} company={c} box={layout[c.id]} splitName={c.id === 'deepmind'} />
        ))}
      </div>
    </section>
  )
}
