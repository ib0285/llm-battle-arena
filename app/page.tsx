import { ArenaBoard } from '@/components/arena/arena-board'
import { ScoreHelp } from '@/components/arena/score-help'
import styles from '@/components/arena/arena.module.css'
import { fetchArenaData, formatUpdated } from '@/lib/arena-data'

export const revalidate = 300

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{ tab?: string }>
}) {
  const params = await searchParams
  const initialTab = params.tab === 'leaders' ? 'leaders' : 'companies'
  const { companies, leaders, posts, usingFallback, updatedAt, mover, topPost } = await fetchArenaData()
  const updatedLabel = formatUpdated(updatedAt)
  const waiting = companies.every((company) => company.status === 'pending')

  return (
    <main className={styles.page} data-arena-source={usingFallback ? 'fallback' : 'live'}>
      <div className={styles.shell}>
        <header className={styles.header}>
          <div>
            <h1>LLM Battle Arena</h1>
            <p className={styles.subtitle}>Who&apos;s winning attention on X · Engagement per follower, rolling 7 days</p>
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
              {updatedLabel ? <span className={styles.updating}>{updatedLabel}</span> : null}
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
          mover={mover}
          topPost={topPost}
          initialTab={initialTab}
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
