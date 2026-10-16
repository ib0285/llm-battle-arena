import { formatIndex, type Leader } from '@/lib/arena-data'
import { TodayDelta } from './today-delta'
import styles from './arena.module.css'

function isRanked(person: Leader) {
  return person.status === 'ok' && person.index !== null
}

export function LeadersBoard({ leaders }: { leaders: Leader[] }) {
  if (leaders.length === 0) {
    return <p className={styles.empty}>Leaders will show up after the next score update.</p>
  }

  const ranked = leaders
    .filter(isRanked)
    .slice()
    .sort((a, b) => (b.index ?? 0) - (a.index ?? 0) || b.reach - a.reach || a.name.localeCompare(b.name))
  const quiet = leaders.filter((person) => !isRanked(person))

  return (
    <div className={styles.leaderWrap}>
      <p className={styles.leaderIntro}>Each person, scored on their own. Reach is the raw 7-day sum, not part of the score.</p>
      {ranked.length > 0 ? (
        <ol className={styles.leaderList}>
          {ranked.map((person, index) => {
            const place = index + 1
            const rowClass = place === 1 ? `${styles.leaderRow} ${styles.leaderRowFirst}` : styles.leaderRow
            return (
              <li key={person.handle} className={rowClass}>
                <span className={styles.leaderRank}>{place}</span>
                <div className={styles.leaderWho}>
                  <p className={styles.leaderNameLine}>
                    <span className={styles.leaderName}>{person.name}</span>
                    {person.biggestReach ? <span className={styles.reachBadge}>Biggest reach</span> : null}
                  </p>
                  <p className={styles.leaderMeta}>
                    <span className={styles.leaderMetaMain}>
                      {person.handle} · {person.companyName}
                    </span>
                    <span className={styles.leaderPosts}>
                      {' '}
                      · {person.posts} posts
                    </span>
                  </p>
                </div>
                <div className={styles.leaderStats}>
                  <div className={styles.leaderStat}>
                    <p className={styles.leaderIndex}>{formatIndex(person.index as number)}</p>
                    <p className={styles.leaderUnit}>Score</p>
                    <TodayDelta value={person.delta} place="inline" />
                  </div>
                  <div className={`${styles.leaderStat} ${styles.leaderStatReach}`}>
                    <p className={styles.leaderIndex}>{person.reachLabel}</p>
                    <p className={styles.leaderUnit}>Reach</p>
                  </div>
                </div>
              </li>
            )
          })}
        </ol>
      ) : null}
      {quiet.length > 0 ? (
        <section className={styles.leaderQuiet} aria-label="Not enough posts this week">
          <h2 className={styles.leaderQuietTitle}>Not enough posts this week</h2>
          <ul className={styles.leaderQuietList}>
            {quiet.map((person) => (
              <li key={person.handle} className={styles.leaderQuietRow}>
                <span className={styles.leaderQuietName}>{person.name}</span>
                <span className={styles.leaderQuietMeta}>
                  {person.handle} · {person.companyName}
                </span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  )
}
