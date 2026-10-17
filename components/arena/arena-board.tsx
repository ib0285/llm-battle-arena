'use client'

import { useEffect, useState } from 'react'
import type { Company, CompanyId, Leader, Mover, Post, TopPost } from '@/lib/arena-data'
import { entityLink, intentUrl, shareText } from '@/lib/share-text'
import { ArenaStage } from './arena-stage'
import { EntityPosts } from './entity-posts'
import { LeadersBoard } from './leaders-board'
import { RecentPosts } from './recent-posts'
import styles from './arena.module.css'

function companyPlace(companies: Company[], id: CompanyId) {
  const ranked = companies
    .filter((company) => company.status === 'ok' && company.index !== null)
    .slice()
    .sort((a, b) => b.score - a.score || b.posts - a.posts)
  const index = ranked.findIndex((company) => company.id === id)
  return index === -1 ? null : index + 1
}

function companyIsBiggest(companies: Company[], id: CompanyId) {
  const top = Math.max(0, ...companies.map((company) => company.reactions || 0))
  const company = companies.find((item) => item.id === id)
  return Boolean(top) && company?.reactions === top
}

function syncUrl(tab: 'companies' | 'leaders', openId: string | null) {
  const params = new URLSearchParams()
  if (tab === 'leaders') params.set('tab', 'leaders')
  if (openId) params.set('open', openId)
  const query = params.toString()
  window.history.replaceState(null, '', query ? `/?${query}` : '/')
}

export function ArenaBoard({
  companies,
  leaders,
  posts,
  leaderPosts,
  mover,
  topPost,
  updatedAt,
  initialTab = 'companies',
  initialOpen = null,
}: {
  companies: Company[]
  leaders: Leader[]
  posts: Post[]
  leaderPosts: Post[]
  mover: Mover | null
  topPost: TopPost | null
  updatedAt: string | null
  initialTab?: 'companies' | 'leaders'
  initialOpen?: string | null
}) {
  const [tab, setTab] = useState<'companies' | 'leaders'>(initialTab)
  const [openId, setOpenId] = useState<string | null>(initialOpen)

  useEffect(() => {
    if (!openId) return
    document.getElementById(`card-${openId}`)?.scrollIntoView({ block: 'nearest' })
  }, [openId])

  function selectTab(next: 'companies' | 'leaders') {
    setTab(next)
    setOpenId(null)
    syncUrl(next, null)
  }

  function toggle(id: string) {
    setOpenId((current) => {
      const next = current === id ? null : id
      syncUrl(tab, next)
      return next
    })
  }

  const openCompany = tab === 'companies' ? companies.find((company) => company.id === openId) : undefined

  return (
    <div>
      <div className={styles.tabs} role="tablist" aria-label="Score boards">
        <a
          href="/"
          role="tab"
          id="tab-companies"
          aria-selected={tab === 'companies'}
          aria-controls="panel-companies"
          className={tab === 'companies' ? `${styles.tab} ${styles.tabOn}` : styles.tab}
          onClick={(event) => {
            event.preventDefault()
            selectTab('companies')
          }}
        >
          Companies
        </a>
        <a
          href="/?tab=leaders"
          role="tab"
          id="tab-leaders"
          aria-selected={tab === 'leaders'}
          aria-controls="panel-leaders"
          className={tab === 'leaders' ? `${styles.tab} ${styles.tabOn}` : styles.tab}
          onClick={(event) => {
            event.preventDefault()
            selectTab('leaders')
          }}
        >
          Leaders
        </a>
      </div>
      {tab === 'companies' ? (
        <div className={styles.board} id="panel-companies" role="tabpanel" aria-labelledby="tab-companies">
          <div className={styles.stageWrap}>
            <ArenaStage companies={companies} selectedId={openId} onSelect={toggle} />
            {openCompany ? (
              <section className={styles.companyPanel} id={`card-${openCompany.id}`} aria-label={`${openCompany.name} posts`}>
                <h3 className={styles.companyPanelTitle}>{openCompany.name}</h3>
                <EntityPosts
                  posts={openCompany.highlights}
                  shareHref={intentUrl(
                    shareText({
                      name: openCompany.name,
                      place: companyPlace(companies, openCompany.id),
                      reactionsLabel: openCompany.reactionsLabel || '0',
                      biggestReach: companyIsBiggest(companies, openCompany.id) && companyPlace(companies, openCompany.id) !== null,
                      link: entityLink('companies', openCompany.id),
                    }),
                  )}
                />
              </section>
            ) : null}
          </div>
          <RecentPosts
            heading="Recent posts"
            posts={posts}
            companies={companies}
            mover={mover}
            topPost={topPost}
            updatedAt={updatedAt}
          />
        </div>
      ) : (
        <div className={styles.board} id="panel-leaders" role="tabpanel" aria-labelledby="tab-leaders">
          <LeadersBoard leaders={leaders} openId={openId} onToggle={toggle} />
          <RecentPosts
            heading="Leaders' recent posts"
            posts={leaderPosts}
            companies={companies}
            mover={null}
            topPost={null}
            updatedAt={updatedAt}
          />
        </div>
      )}
    </div>
  )
}
