import { ArenaBoard } from '@/components/arena/arena-board'
import { resolveOpen } from '@/lib/resolve-open'
import { ScoreHelp } from '@/components/arena/score-help'
import styles from '@/components/arena/arena.module.css'
import { UpdatedLabel } from '@/components/arena/refresh-scores'
import { fetchArenaData } from '@/lib/arena-data'

export const revalidate = 300

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{ tab?: string; open?: string }>
}) {
  const params = await searchParams
  const { companies, leaders, posts, leaderPosts, usingFallback, updatedAt, mover, topPost } = await fetchArenaData()
  const { tab: initialTab, openId } = resolveOpen(params.tab, params.open, companies, leaders)
  const waiting = companies.every((company) => company.status === 'pending')

  return (
    <main className={styles.page} data-arena-source={usingFallback ? 'fallback' : 'live'}>
      <div className={styles.shell}>
        <header className={styles.header}>
          <div>
            <h1>LLM Battle Arena</h1>
            <p className={styles.subtitle}>
              Who gets the most reaction per follower on X this week. Tap anyone to see their posts.
            </p>
            <ScoreHelp />
          </div>
          <div className={styles.status} role="status" aria-live="polite">
            <div className={styles.liveRow}>
              <span className={styles.liveBadge}>
                <span className={styles.pingWrap}>
                  <span className={styles.ping} />
                  <span className={styles.pingDot} />
                </span>
                LIVE
              </span>
              <UpdatedLabel updatedAt={updatedAt} />
            </div>
          </div>
        </header>
        {usingFallback ? (
          <p className={styles.notice} role="status">
            Live scores could not be loaded, so this page is showing the last saved copy.
          </p>
        ) : null}
        {waiting ? (
          <p className={styles.notice} role="status">
            The 7-day score will show up after the next data update.
          </p>
        ) : null}
        <ArenaBoard
          companies={companies}
          leaders={leaders}
          posts={posts}
          leaderPosts={leaderPosts}
          mover={mover}
          topPost={topPost}
          updatedAt={updatedAt}
          initialTab={initialTab}
          initialOpen={openId}
        />
        <footer className={styles.footer}>
          <p>
            A fun side project by Bakhytzhan Ibrayev ·{' '}
            <a href="https://x.com/BakhytzhanIbra1" target="_blank" rel="noopener noreferrer">
              @BakhytzhanIbra1
            </a>{' '}
            · not affiliated with any lab
          </p>
          <a href="https://x.com/BakhytzhanIbra1" target="_blank" rel="noopener noreferrer">
            Suggest an account
          </a>
        </footer>
      </div>
    </main>
  )
}
