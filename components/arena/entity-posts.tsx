'use client'

import { useState } from 'react'
import { Heart, MessageCircle, Repeat2 } from 'lucide-react'
import { formatCount, timeAgo, type EntityPost } from '@/lib/arena-data'
import styles from './arena.module.css'

const IMAGE_URL = /https?:\/\/\S+\.(?:jpe?g|png|gif|webp)(?:\?\S*)?/i

function PostMedia({ text }: { text: string }) {
  const [hidden, setHidden] = useState(false)
  const match = text.match(IMAGE_URL)
  if (!match || hidden) return null
  return (
    <img
      className={styles.entityMedia}
      src={match[0]}
      alt=""
      onError={() => setHidden(true)}
    />
  )
}

export function EntityPosts({ posts, shareHref }: { posts: EntityPost[]; shareHref: string }) {
  const [mode, setMode] = useState<'top' | 'new'>('top')
  const [more, setMore] = useState(false)
  const sorted = posts.slice().sort((a, b) => {
    if (mode === 'new') return b.at.localeCompare(a.at)
    const engagement = (post: EntityPost) => post.likes + post.reposts + post.replies
    return engagement(b) - engagement(a) || b.at.localeCompare(a.at)
  })
  const shown = more ? sorted : sorted.slice(0, 3)

  return (
    <div className={styles.entityPanel}>
      <div className={styles.sortRow}>
        <button
          type="button"
          className={mode === 'top' ? `${styles.sortBtn} ${styles.sortOn}` : styles.sortBtn}
          aria-pressed={mode === 'top'}
          onClick={() => setMode('top')}
        >
          Top
        </button>
        <span className={styles.sortBar} aria-hidden="true">
          |
        </span>
        <button
          type="button"
          className={mode === 'new' ? `${styles.sortBtn} ${styles.sortOn}` : styles.sortBtn}
          aria-pressed={mode === 'new'}
          onClick={() => setMode('new')}
        >
          Newest
        </button>
      </div>
      {shown.length === 0 ? (
        <p className={styles.entityEmpty}>No posts in the last 7 days.</p>
      ) : (
        <ul className={styles.entityList}>
          {shown.map((post, index) => {
            const when = timeAgo(post.at)
            return (
              <li key={`${post.at}-${index}`} className={styles.entityPost}>
                <p className={styles.entityText}>{post.text}</p>
                <PostMedia text={post.text} />
                <p className={styles.entityCounts}>
                  <span className={styles.entityStat}>
                    <Heart aria-hidden="true" />
                    <span className={styles.srOnly}>Likes</span>
                    {formatCount(post.likes)}
                  </span>
                  <span className={styles.entityStat}>
                    <Repeat2 aria-hidden="true" />
                    <span className={styles.srOnly}>Reposts</span>
                    {formatCount(post.reposts)}
                  </span>
                  <span className={styles.entityStat}>
                    <MessageCircle aria-hidden="true" />
                    <span className={styles.srOnly}>Replies</span>
                    {formatCount(post.replies)}
                  </span>
                  {when ? <span className={styles.entityWhen}>{when}</span> : null}
                  {post.url ? (
                    <a className={styles.entityView} href={post.url} target="_blank" rel="noopener noreferrer">
                      View on X
                    </a>
                  ) : null}
                </p>
              </li>
            )
          })}
        </ul>
      )}
      <div className={styles.entityActions}>
        {posts.length > 3 ? (
          <button type="button" className={styles.showMore} onClick={() => setMore((open) => !open)}>
            {more ? 'Show less' : 'Show more'}
          </button>
        ) : null}
        <a className={styles.shareBtn} href={shareHref} target="_blank" rel="noopener noreferrer">
          Share on X
        </a>
      </div>
    </div>
  )
}
