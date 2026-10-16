import { BadgeCheck, ExternalLink, Heart, MessageCircle, Repeat2, RotateCw } from 'lucide-react'
import type { Company, Post } from '@/lib/arena-data'
import { BrandLogo } from './brand-logo'
import styles from './arena.module.css'

function XMark({ className }: { className?: string }) {
  const classes = className ? `${styles.xMark} ${className}` : styles.xMark
  return <span aria-hidden="true" className={classes} />
}

export function RecentPosts({ posts, companies }: { posts: Post[]; companies: Company[] }) {
  const byId = new Map(companies.map((company) => [company.id, company]))

  return (
    <aside className={styles.feed} aria-labelledby="recent-posts-title">
      <header className={styles.feedHead}>
        <h2 id="recent-posts-title">
          <XMark />
          Recent Posts
        </h2>
        <button type="button" className={styles.refresh} aria-label="Refresh posts">
          <RotateCw className={styles.refreshIcon} aria-hidden="true" />
        </button>
      </header>
      {posts.length === 0 ? (
        <p className={styles.empty}>No posts yet. They will show up here after they are added to the score file.</p>
      ) : (
        <ul className={styles.feedList}>
          {posts.map((post) => {
            const company = byId.get(post.companyId)
            return (
              <li key={post.id} className={styles.post} data-post={post.id}>
                <div className={styles.postRow}>
                  <div className={styles.postAvatar}>
                    {company ? <BrandLogo company={company} className={styles.avatarLogo} /> : null}
                  </div>
                  <div className={styles.postBody}>
                    <div className={styles.nameRow}>
                      <span className={styles.postName}>{post.name}</span>
                      <BadgeCheck className={styles.verified} strokeWidth={2.5} aria-label="Verified" />
                      <span className={styles.handleLine}>
                        {post.handle}
                        {post.time ? ` · ${post.time}` : ''}
                      </span>
                    </div>
                    <p className={styles.postText}>{post.text}</p>
                    <div className={styles.stats}>
                      <span className={styles.stat}>
                        <MessageCircle aria-hidden="true" />
                        <span className={styles.srOnly}>Replies</span>
                        {post.replies}
                      </span>
                      <span className={styles.stat}>
                        <Repeat2 aria-hidden="true" />
                        <span className={styles.srOnly}>Reposts</span>
                        {post.reposts}
                      </span>
                      <span className={styles.stat}>
                        <Heart aria-hidden="true" />
                        <span className={styles.srOnly}>Likes</span>
                        {post.likes}
                      </span>
                    </div>
                  </div>
                </div>
                <XMark className={styles.cornerX} />
              </li>
            )
          })}
        </ul>
      )}
      <a className={styles.more} href="https://x.com/search?q=AI" target="_blank" rel="noopener noreferrer">
        View more on X
        <ExternalLink className={styles.moreIcon} aria-hidden="true" />
      </a>
    </aside>
  )
}
