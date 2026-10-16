import type { CSSProperties } from 'react'
import type { Company, Post } from '@/lib/arena-data'
import { BrandLogo } from './brand-logo'
import styles from './arena.module.css'

export function RecentPosts({ posts, companies }: { posts: Post[]; companies: Company[] }) {
  const byId = new Map(companies.map((company) => [company.id, company]))

  return (
    <aside className={styles.feed} aria-label="Recent posts">
      <header className={styles.feedHead}>
        <h2>Recent Posts</h2>
        <span className={styles.live}>
          <span className={`${styles.dot} ${styles.liveDot}`} />
          Live
        </span>
      </header>
      {posts.length === 0 ? (
        <p className={styles.empty}>No posts yet. They will show up here after they are added to the score file.</p>
      ) : (
        <ul className={styles.feedList}>
          {posts.map((post) => {
            const company = byId.get(post.companyId)
            const style = { '--accent': company?.accent ?? '#e9b949' } as CSSProperties
            return (
              <li key={post.id} className={styles.post} data-post={post.id} style={style}>
                <div className={styles.postTop}>
                  {company ? (
                    <BrandLogo company={company} className={styles.feedLogo} />
                  ) : (
                    <span className={styles.feedLogo} aria-hidden="true" />
                  )}
                  <p className={styles.postMeta}>
                    <span className={styles.postName}>{post.name}</span>
                    {post.inlineHandle ? <span className={styles.postHandle}> {post.handle}</span> : null}
                    {post.time ? <span className={styles.postTime}> · {post.time}</span> : null}
                    {post.inlineHandle ? null : <span className={styles.postHandleBlock}>{post.handle}</span>}
                  </p>
                </div>
                <p className={styles.postText}>{post.text}</p>
                <p className={styles.stats}>
                  <span>
                    <span className={styles.statLabel}>Replies</span> {post.replies}
                  </span>
                  <span>
                    <span className={styles.statLabel}>Reposts</span> {post.reposts}
                  </span>
                  <span>
                    <span className={styles.statLabel}>Likes</span> {post.likes}
                  </span>
                </p>
              </li>
            )
          })}
        </ul>
      )}
    </aside>
  )
}
