import type { Company, Post } from '@/lib/arena-data'
import { CompanyLogo } from './company-card'
import styles from './arena.module.css'

export function RecentPosts({ posts, companies }: { posts: Post[]; companies: Company[] }) {
  const byId = new Map(companies.map((company) => [company.id, company]))

  return (
    <section className={styles.posts} aria-label="Recent posts">
      <div className={styles.postsHead}>
        <h2>Recent Posts</h2>
      </div>
      {posts.length === 0 ? (
        <p className={styles.empty}>No posts yet. They will show up here after they are added to the score file.</p>
      ) : (
        <ul className={styles.postList}>
          {posts.map((post) => {
            const company = byId.get(post.companyId)
            return (
              <li key={post.id} className={styles.post} data-post={post.id} style={{ ['--accent' as string]: company?.accent ?? '#e9b949' }}>
                <div className={styles.postMain}>
                  {company ? <CompanyLogo company={company} /> : <span className={styles.logoFallback} aria-hidden="true" />}
                  <div className={styles.postBody}>
                    <p className={styles.postMeta}>
                      <span className={styles.postName}>{post.name}</span>
                      {post.inlineHandle ? <span className={styles.postHandle}> {post.handle}</span> : null}
                      {post.time ? <span className={styles.postTime}> · {post.time}</span> : null}
                      {post.inlineHandle ? null : <span className={styles.postHandleBlock}>{post.handle}</span>}
                    </p>
                    <p className={styles.postText}>{post.text}</p>
                    <p className={styles.engagement}>
                      <span>
                        <span className={styles.engagementLabel}>Replies</span> {post.replies}
                      </span>
                      <span>
                        <span className={styles.engagementLabel}>Reposts</span> {post.reposts}
                      </span>
                      <span>
                        <span className={styles.engagementLabel}>Likes</span> {post.likes}
                      </span>
                    </p>
                  </div>
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
