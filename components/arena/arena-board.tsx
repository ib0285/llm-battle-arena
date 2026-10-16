'use client'

import { useState } from 'react'
import type { Company, Leader, Mover, Post, TopPost } from '@/lib/arena-data'
import { ArenaStage } from './arena-stage'
import { LeadersBoard } from './leaders-board'
import { RecentPosts } from './recent-posts'
import styles from './arena.module.css'

export function ArenaBoard({
  companies,
  leaders,
  posts,
  mover,
  topPost,
  initialTab = 'companies',
}: {
  companies: Company[]
  leaders: Leader[]
  posts: Post[]
  mover: Mover | null
  topPost: TopPost | null
  initialTab?: 'companies' | 'leaders'
}) {
  const [tab, setTab] = useState<'companies' | 'leaders'>(initialTab)

  return (
    <div>
      <div className={styles.tabs} role="tablist" aria-label="Score boards">
        <button
          type="button"
          role="tab"
          id="tab-companies"
          aria-selected={tab === 'companies'}
          aria-controls="panel-companies"
          className={tab === 'companies' ? `${styles.tab} ${styles.tabOn}` : styles.tab}
          onClick={() => setTab('companies')}
        >
          Companies
        </button>
        <button
          type="button"
          role="tab"
          id="tab-leaders"
          aria-selected={tab === 'leaders'}
          aria-controls="panel-leaders"
          className={tab === 'leaders' ? `${styles.tab} ${styles.tabOn}` : styles.tab}
          onClick={() => setTab('leaders')}
        >
          Leaders
        </button>
      </div>
      {tab === 'companies' ? (
        <div className={styles.board} id="panel-companies" role="tabpanel" aria-labelledby="tab-companies">
          <div className={styles.stageWrap}>
            <ArenaStage companies={companies} />
          </div>
          <RecentPosts posts={posts} companies={companies} mover={mover} topPost={topPost} />
        </div>
      ) : (
        <div id="panel-leaders" role="tabpanel" aria-labelledby="tab-leaders">
          <LeadersBoard leaders={leaders} />
        </div>
      )}
    </div>
  )
}
