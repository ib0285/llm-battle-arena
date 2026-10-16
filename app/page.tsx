import { ArenaStage } from '@/components/arena/arena-stage'
import { RecentPosts } from '@/components/arena/recent-posts'
import styles from '@/components/arena/arena.module.css'
import { fetchArenaData } from '@/lib/arena-data'

export const revalidate = 300

export default async function HomePage() {
  const { companies, posts, usingFallback } = await fetchArenaData()

  return (
    <main className={styles.page} data-arena-source={usingFallback ? 'fallback' : 'live'}>
      <div className={styles.shell}>
        <header className={styles.header}>
          <div>
            <h1>LLM Battle Arena</h1>
            <p className={styles.subtitle}>
              Live race of posts on X · Score = average likes + reposts + replies per post, last 24 hours
            </p>
          </div>
          <div className={styles.status} role="status" aria-live="polite">
            <span className={styles.liveBadge}>
              <span className={styles.pingWrap}>
                <span className={styles.ping} />
                <span className={styles.pingDot} />
              </span>
              LIVE
            </span>
            <span className={styles.updating}>Updating live</span>
          </div>
        </header>
        {usingFallback ? (
          <p className={styles.notice} role="status">
            Live scores could not be loaded, so this page is showing the last saved copy.
          </p>
        ) : null}
        <div className={styles.board}>
          <div className={styles.stageWrap}>
            <ArenaStage companies={companies} />
          </div>
          <RecentPosts posts={posts} companies={companies} />
        </div>
      </div>
    </main>
  )
}
