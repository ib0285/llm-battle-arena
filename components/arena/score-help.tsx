'use client'

import { useEffect, useId, useState } from 'react'
import { createPortal } from 'react-dom'
import changelog from '@/changelog.json'
import styles from './arena.module.css'

const SUGGEST_URL =
  'https://x.com/intent/post?text=@BakhytzhanIbra1%20suggestion%20for%20LLM%20Battle%20Arena:%20'

type ChangelogEntry = {
  date: string
  change: string
  credit?: string
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

function formatDay(iso: string) {
  const [year, month, day] = iso.split('-').map(Number)
  if (!year || !month || !day) return iso
  return `${MONTHS[month - 1]} ${day}`
}

function creditHandle(credit: string) {
  const handle = credit.trim().replace(/^@/, '')
  return handle ? `@${handle}` : ''
}

function grouped(entries: ChangelogEntry[]) {
  const groups: { date: string; items: ChangelogEntry[] }[] = []
  for (const entry of entries) {
    const last = groups[groups.length - 1]
    if (last && last.date === entry.date) last.items.push(entry)
    else groups.push({ date: entry.date, items: [entry] })
  }
  return groups
}

export function ScoreHelp() {
  const [open, setOpen] = useState(false)
  const titleId = useId()

  useEffect(() => {
    if (!open) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false)
    }
    const previous = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    window.addEventListener('keydown', onKey)
    return () => {
      document.body.style.overflow = previous
      window.removeEventListener('keydown', onKey)
    }
  }, [open])

  const dialog = open ? (
    <div className={styles.modalBackdrop} onClick={() => setOpen(false)}>
      <div
        className={styles.modal}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(event) => event.stopPropagation()}
      >
        <div className={styles.modalBar}>
          <h2 id={titleId}>How it&apos;s scored</h2>
          <button type="button" className={styles.modalClose} onClick={() => setOpen(false)}>
            Close
          </button>
        </div>
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
            <section className={styles.changelog} aria-label="Changelog">
              <h3>Changelog</h3>
              {grouped(changelog as ChangelogEntry[]).map((group) => (
                <div key={group.date} className={styles.changelogGroup}>
                  <div className={styles.changelogDate}>{formatDay(group.date)}</div>
                  <ul className={styles.changelogList}>
                    {group.items.map((entry) => {
                      const credit = entry.credit ? creditHandle(entry.credit) : ''
                      return (
                        <li key={entry.change} className={styles.changelogItem}>
                          <span className={styles.changelogChange}>{entry.change}</span>
                          {credit ? <span className={styles.changelogCredit}>suggested by {credit}</span> : null}
                        </li>
                      )
                    })}
                  </ul>
                </div>
              ))}
            </section>
            <a className={styles.suggestFix} href={SUGGEST_URL} target="_blank" rel="noopener noreferrer">
              Suggest a fix to the method
            </a>
          </div>
        </div>
  ) : null

  return (
    <>
      <button type="button" className={styles.infoLink} onClick={() => setOpen(true)}>
        How it&apos;s scored ⓘ
      </button>
      {dialog && typeof document !== 'undefined' ? createPortal(dialog, document.body) : null}
    </>
  )
}
