'use client'

import { formatIndex, leaderKey, type Leader } from '@/lib/arena-data'
import { entityLink, intentUrl, shareText } from '@/lib/share-text'
import { EntityPosts } from './entity-posts'
import { TodayDelta } from './today-delta'
import styles from './arena.module.css'

function isRanked(person: Leader) {
  return person.status === 'ok' && person.index !== null
}

function shareHref(person: Leader, place: number | null) {
  const id = leaderKey(person.handle)
  return intentUrl(
    shareText({
      name: person.name,
      place,
      reactionsLabel: person.reachLabel,
      biggestReach: person.biggestReach && place !== null,
      link: entityLink('leaders', id),
    }),
  )
}

export function LeadersBoard({
  leaders,
  openId,
  onToggle,
}: {
  leaders: Leader[]
  openId: string | null
  onToggle: (id: string) => void
}) {
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
      {ranked.length > 0 ? (
        <ol className={styles.leaderList}>
          {ranked.map((person, index) => {
            const place = index + 1
            const id = leaderKey(person.handle)
            const open = openId === id
            const cardClass = place === 1 ? `${styles.leaderCard} ${styles.leaderCardFirst}` : styles.leaderCard
            return (
              <li key={person.handle} id={`card-${id}`} className={open ? `${cardClass} ${styles.leaderCardOpen}` : cardClass}>
                <button
                  type="button"
                  className={styles.leaderRow}
                  aria-expanded={open}
                  onClick={() => onToggle(id)}
                >
                  <span className={styles.leaderRank}>{place}</span>
                  <span className={styles.leaderWho}>
                    <span className={styles.leaderNameLine}>
                      <span className={styles.leaderName}>{person.name}</span>
                    </span>
                    <span className={styles.leaderMeta}>
                      <span className={styles.leaderMetaMain}>
                        {person.companyName} · {person.posts} posts
                      </span>
                      {person.biggestReach ? <span className={styles.reachBadge}>Biggest reach</span> : null}
                    </span>
                  </span>
                  <span className={styles.leaderStats}>
                    <span className={styles.leaderStat}>
                      <span className={styles.leaderIndex}>{formatIndex(person.index as number)}</span>
                      <span className={styles.leaderUnit}>This week&apos;s score</span>
                      <TodayDelta value={person.delta} place="inline" />
                    </span>
                    <span className={`${styles.leaderStat} ${styles.leaderStatReach}`}>
                      <span className={styles.leaderIndex}>{person.reachLabel}</span>
                      <span className={styles.leaderUnit}>Total reactions</span>
                    </span>
                  </span>
                </button>
                {open ? <EntityPosts posts={person.highlights} shareHref={shareHref(person, place)} /> : null}
              </li>
            )
          })}
        </ol>
      ) : null}
      {quiet.length > 0 ? (
        <section className={styles.leaderQuiet} aria-label="Not enough posts this week">
          <h2 className={styles.leaderQuietTitle}>Not enough posts this week</h2>
          <ul className={styles.leaderQuietList}>
            {quiet.map((person) => {
              const id = leaderKey(person.handle)
              const open = openId === id
              return (
                <li key={person.handle} id={`card-${id}`} className={styles.leaderQuietItem}>
                  <button type="button" className={styles.leaderQuietRow} aria-expanded={open} onClick={() => onToggle(id)}>
                    <span className={styles.leaderQuietName}>{person.name}</span>
                    <span className={styles.leaderQuietMeta}>
                      {person.companyName} · {person.posts} posts
                    </span>
                  </button>
                  {open ? <EntityPosts posts={person.highlights} shareHref={shareHref(person, null)} /> : null}
                </li>
              )
            })}
          </ul>
        </section>
      ) : null}
    </div>
  )
}
