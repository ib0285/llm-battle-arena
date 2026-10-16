import { formatIndex, type Leader } from '@/lib/arena-data'
import { TodayDelta } from './today-delta'
import styles from './arena.module.css'

export function LeadersBoard({ leaders }: { leaders: Leader[] }) {
  if (leaders.length === 0) {
    return <p className={styles.empty}>Leaders will show up after the next score update.</p>
  }

  let rank = 0

  return (
    <div className={styles.leaderWrap}>
      <p className={styles.leaderIntro}>Each person, scored on their own. Total reach is the raw 7-day sum, not part of the index.</p>
      <ol className={styles.leaderList}>
        {leaders.map((person) => {
          const qualified = person.status === 'ok' && person.index !== null
          if (qualified) rank += 1
          return (
            <li
              key={person.handle}
              className={person.biggestReach ? `${styles.leaderRow} ${styles.leaderRowHot}` : styles.leaderRow}
            >
              <span className={styles.leaderRank}>{qualified ? rank : '—'}</span>
              <div className={styles.leaderWho}>
                <p className={styles.leaderName}>{person.name}</p>
                <p className={styles.leaderMeta}>
                  {person.handle} · {person.companyName}
                </p>
              </div>
              <div className={styles.leaderScore}>
                <p className={styles.leaderIndex}>{qualified ? formatIndex(person.index as number) : '—'}</p>
                <p className={styles.leaderUnit}>{person.status === 'not_enough_posts' ? 'not enough posts' : 'score · 7d'}</p>
                {qualified ? <TodayDelta value={person.delta} place="inline" /> : null}
              </div>
              <div className={styles.leaderPosts}>
                {person.posts} posts · 7d
              </div>
              <div className={styles.leaderReach}>
                <p className={styles.reachKicker}>Total reach</p>
                <p className={styles.reachValue}>
                  {person.reachLabel}
                  {person.biggestReach ? <span className={styles.reachBadge}>Biggest reach</span> : null}
                </p>
              </div>
            </li>
          )
        })}
      </ol>
    </div>
  )
}
