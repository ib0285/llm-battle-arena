import type { CSSProperties } from 'react'
import { BadgeCheck, ExternalLink, Heart, MessageCircle, Repeat2 } from 'lucide-react'
import type { Company, Mover, Post, TopPost } from '@/lib/arena-data'
import { BrandLogo } from './brand-logo'
import { RefreshScores } from './refresh-scores'
import styles from './arena.module.css'

function TopPostCard({ post, company }: { post: TopPost; company?: Company }) {
  return (
    <article
      className={styles.topPost}
      style={{ '--accent': company?.accent ?? '#e9b949' } as CSSProperties}
      aria-label="Top post today"
    >
      <p className={styles.topPostLabel}>
        <span aria-hidden="true">🔥 </span>
        Top post today
      </p>
      <div className={styles.postRow}>
        <div className={styles.postAvatar}>
          {company ? <BrandLogo company={company} className={styles.avatarLogo} /> : null}
        </div>
        <div className={styles.postBody}>
          <div className={styles.nameRow}>
            <span className={styles.postName}>{post.author}</span>
            <BadgeCheck className={styles.verified} strokeWidth={2.5} aria-label="Verified" />
            <span className={styles.topPostLab}>{post.lab}</span>
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
            {post.url ? (
              <a className={styles.viewOnX} href={post.url} target="_blank" rel="noopener noreferrer">
                View on X ↗
              </a>
            ) : null}
          </div>
        </div>
      </div>
    </article>
  )
}

function XMark({ className }: { className?: string }) {
  const classes = className ? `${styles.xMark} ${className}` : styles.xMark
  return <span aria-hidden="true" className={classes} />
}

export function RecentPosts({
  posts,
  companies,
  mover,
  topPost,
  heading,
  updatedAt,
}: {
  posts: Post[]
  companies: Company[]
  mover: Mover | null
  topPost: TopPost | null
  heading: string
  updatedAt: string | null
}) {
  const byId = new Map(companies.map((company) => [company.id, company]))
  const changeClass = mover && mover.change < 0 ? styles.down : styles.up
  const changeText = mover ? `${mover.change > 0 ? '+' : ''}${mover.change}%` : ''

  return (
    <aside className={styles.feed} aria-labelledby="recent-posts-title">
      {mover ? (
        <div className={styles.mover}>
          <p className={styles.moverTitle}>
            <span aria-hidden="true">🚀 </span>
            Biggest mover {mover.period === 'week' ? 'this week' : 'today'} · {mover.name}{' '}
            <span className={changeClass}>{changeText}</span>
          </p>
        </div>
      ) : null}
      <header className={styles.feedHead}>
        <div className={styles.feedHeadRow}>
          <h2 id="recent-posts-title">
            <XMark />
            {heading}
          </h2>
          <RefreshScores updatedAt={updatedAt} />
        </div>
      </header>
      {topPost ? <TopPostCard post={topPost} company={byId.get(topPost.companyId)} /> : null}
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
                      {post.url ? (
                        <a className={styles.viewOnX} href={post.url} target="_blank" rel="noopener noreferrer">
                          View on X ↗
                        </a>
                      ) : null}
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
