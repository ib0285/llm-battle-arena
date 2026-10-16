'use client'

import { useEffect, useId, useState } from 'react'
import styles from './arena.module.css'

export function ScoreHelp() {
  const [open, setOpen] = useState(false)
  const titleId = useId()

  useEffect(() => {
    if (!open) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open])

  return (
    <>
      <button type="button" className={styles.infoLink} onClick={() => setOpen(true)}>
        How it&apos;s scored ⓘ
      </button>
      {open ? (
        <div className={styles.modalBackdrop} onClick={() => setOpen(false)}>
          <div
            className={styles.modal}
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            onClick={(event) => event.stopPropagation()}
          >
            <h2 id={titleId}>How it&apos;s scored</h2>
            <p>
              For each account we add likes, reposts, and replies on its original posts from the last 7 days, divide by
              the number of posts, then divide by followers and multiply by 1,000. That is the average engagement per
              post for every 1,000 followers.
            </p>
            <p>
              <strong>Companies</strong> uses only the official lab accounts. A company&apos;s score is the average of
              those account numbers, weighted by how many posts each account made, so a busier account counts more.
              Personal accounts are not mixed in.
            </p>
            <p>
              <strong>Leaders</strong> scores each person on their own with that same per-follower number, then scales
              the people against each other. The best person is 10.0.
            </p>
            <p>
              Both boards turn the number into an index from 1.0 to 10.0. Anyone with fewer than 3 posts in the 7 days
              says &quot;not enough posts&quot; and ranks last. The arrow is the percent change since about a day ago.
            </p>
            <p>
              Leaders also show <strong>Total reach</strong>: the plain sum of likes, reposts, and replies over those 7
              days. It sits beside the index. The two numbers are not blended.
            </p>
            <p className={styles.modalNote}>Just for fun, not a measure of which AI is best.</p>
            <button type="button" className={styles.modalClose} onClick={() => setOpen(false)}>
              Close
            </button>
          </div>
        </div>
      ) : null}
    </>
  )
}
