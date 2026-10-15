import { ArenaStage } from '@/components/arena/arena-stage'
import { RecentPosts } from '@/components/arena/recent-posts'
import styles from '@/components/arena/arena.module.css'
import { fetchArenaData } from '@/lib/arena-data'

export const revalidate = 300

export default async function HomePage() {
  const { companies, posts, usingFallback } = await fetchArenaData()

  return (
    <main className={styles.page} data-arena-source={usingFallback ? 'fallback' : 'live'}>
      <header className={styles.header}>
        <p className={styles.kicker}>LLM Battle Arena</p>
      </header>
      {usingFallback ? (
        <p className={styles.notice} role="status">
          Live scores could not be loaded, so this page is showing the last saved copy.
        </p>
      ) : null}
      <ArenaStage companies={companies} />
      <RecentPosts posts={posts} companies={companies} />
    </main>
  )
}
