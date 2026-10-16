// Scores are loaded on the server from the GitHub file, then passed into
// the page. The browser does not fetch this itself.

const GITHUB_DATA_URL =
  process.env.ARENA_SCORES_URL ||
  'https://raw.githubusercontent.com/ib0285/llm-battle-arena/main/scores.json'

export const REVALIDATE_SECONDS = 300

export type CompanyId = 'xai' | 'openai' | 'meta' | 'anthropic' | 'deepmind'

export type CompanyStatus = 'ok' | 'not_enough_posts' | 'pending'

export type Company = {
  id: CompanyId
  name: string
  score: number
  posts: number
  progress: number
  accent: string
  logo: string
  logoMode: 'mask' | 'image'
  logoColor?: string
  index: number | null
  delta: number | null
  status: CompanyStatus
}

export type Post = {
  id: string
  companyId: CompanyId
  name: string
  handle: string
  time: string
  text: string
  replies: string
  reposts: string
  likes: string
  inlineHandle: boolean
  url?: string
}

export type TopPost = {
  author: string
  handle: string
  lab: string
  companyId: CompanyId
  text: string
  likes: string
  reposts: string
  replies: string
  engagement: number
  url?: string
  createdAt: string
  time: string
}

export type Mover = {
  companyId: CompanyId
  name: string
  change: number
  period: 'week' | 'today'
}

export type Leader = {
  handle: string
  name: string
  companyId: CompanyId
  companyName: string
  score: number
  index: number | null
  posts: number
  progress: number
  delta: number | null
  status: CompanyStatus
  reach: number
  reachLabel: string
  biggestReach: boolean
}

export type ArenaData = {
  companies: Company[]
  posts: Post[]
  leaders: Leader[]
  usingFallback: boolean
  updatedAt: string | null
  mover: Mover | null
  topPost: TopPost | null
}

type CompanyDefaults = {
  id: CompanyId
  name: string
  accent: string
  logo: string
  logoMode: 'mask' | 'image'
  logoColor?: string
}

const DISPLAY: Record<CompanyId, CompanyDefaults> = {
  xai: {
    id: 'xai',
    name: 'xAI',
    accent: '#e9b949',
    logo: '/logos/xai.svg',
    logoMode: 'mask',
    logoColor: 'linear-gradient(160deg,#ffe08a,#d9a032)',
  },
  openai: {
    id: 'openai',
    name: 'OpenAI',
    accent: '#34d399',
    logo: '/logos/openai.svg',
    logoMode: 'mask',
    logoColor: '#ffffff',
  },
  meta: {
    id: 'meta',
    name: 'Meta',
    accent: '#3b9cf6',
    logo: '/logos/meta.svg',
    logoMode: 'image',
  },
  anthropic: {
    id: 'anthropic',
    name: 'Anthropic',
    accent: '#9f6bf5',
    logo: '/logos/anthropic.svg',
    logoMode: 'mask',
    logoColor: 'linear-gradient(160deg,#c4a1ff,#8b5cf6)',
  },
  deepmind: {
    id: 'deepmind',
    name: 'Google DeepMind',
    accent: '#3b82f6',
    logo: '/logos/deepmind.svg',
    logoMode: 'mask',
    logoColor: 'linear-gradient(135deg,#4f8df7 0%,#4f8df7 45%,#f7c544 55%,#f7c544 100%)',
  },
}

const NAME_TO_ID: Record<string, CompanyId> = {
  xai: 'xai',
  openai: 'openai',
  meta: 'meta',
  anthropic: 'anthropic',
  deepmind: 'deepmind',
  'google deepmind': 'deepmind',
}

const fallbackCompanies: Company[] = [
  {
    id: 'xai',
    name: 'xAI',
    score: 8.4,
    index: 8.4,
    posts: 28,
    progress: 0.84,
    delta: 6,
    status: 'ok',
    accent: '#e9b949',
    logo: '/logos/xai.svg',
    logoMode: 'mask',
    logoColor: 'linear-gradient(160deg,#ffe08a,#d9a032)',
  },
  {
    id: 'openai',
    name: 'OpenAI',
    score: 7.2,
    index: 7.2,
    posts: 19,
    progress: 0.72,
    delta: -3,
    status: 'ok',
    accent: '#34d399',
    logo: '/logos/openai.svg',
    logoMode: 'mask',
    logoColor: '#ffffff',
  },
  {
    id: 'meta',
    name: 'Meta',
    score: 4.6,
    index: 4.6,
    posts: 11,
    progress: 0.46,
    delta: 2,
    status: 'ok',
    accent: '#3b9cf6',
    logo: '/logos/meta.svg',
    logoMode: 'image',
  },
  {
    id: 'anthropic',
    name: 'Anthropic',
    score: 10,
    index: 10,
    posts: 16,
    progress: 1,
    delta: 12,
    status: 'ok',
    accent: '#9f6bf5',
    logo: '/logos/anthropic.svg',
    logoMode: 'mask',
    logoColor: 'linear-gradient(160deg,#c4a1ff,#8b5cf6)',
  },
  {
    id: 'deepmind',
    name: 'Google DeepMind',
    score: 0,
    index: null,
    posts: 2,
    progress: 0,
    delta: null,
    status: 'not_enough_posts',
    accent: '#3b82f6',
    logo: '/logos/deepmind.svg',
    logoMode: 'mask',
    logoColor: 'linear-gradient(135deg,#4f8df7 0%,#4f8df7 45%,#f7c544 55%,#f7c544 100%)',
  },
]

const fallbackPosts: Post[] = [
  {
    id: 'p1',
    companyId: 'anthropic',
    name: 'Anthropic',
    handle: '@AnthropicAI',
    time: '42m',
    text: 'Applications are now open for two new Anthropic Fellowships.',
    replies: '214',
    reposts: '1.1K',
    likes: '6.4K',
    inlineHandle: false,
    url: 'https://x.com/AnthropicAI',
  },
  {
    id: 'p2',
    companyId: 'xai',
    name: 'Elon Musk',
    handle: '@elonmusk',
    time: '3h',
    text: 'The whole world will watch this',
    replies: '4.8K',
    reposts: '9.2K',
    likes: '61K',
    inlineHandle: true,
    url: 'https://x.com/elonmusk',
  },
  {
    id: 'p3',
    companyId: 'openai',
    name: 'OpenAI',
    handle: '@OpenAI',
    time: '5h',
    text: 'Day 11. We’ve landed a series of changes and more compute to decrease capacity issues.',
    replies: '86',
    reposts: '142',
    likes: '1.3K',
    inlineHandle: false,
    url: 'https://x.com/OpenAI',
  },
  {
    id: 'p4',
    companyId: 'meta',
    name: 'AI at Meta',
    handle: '@AIatMeta',
    time: '1d',
    text: 'Today we’re releasing Muse Spark Open.',
    replies: '338',
    reposts: '1.6K',
    likes: '8.7K',
    inlineHandle: false,
    url: 'https://x.com/AIatMeta',
  },
]

const fallbackLeaders: Leader[] = [
  {
    handle: '@sama',
    name: 'Sam Altman',
    companyId: 'openai',
    companyName: 'OpenAI',
    score: 10,
    index: 10,
    posts: 9,
    progress: 1,
    delta: 6,
    status: 'ok',
    reach: 12_300_000,
    reachLabel: '12.3M',
    biggestReach: true,
  },
  {
    handle: '@elonmusk',
    name: 'Elon Musk',
    companyId: 'xai',
    companyName: 'xAI',
    score: 7.4,
    index: 7.4,
    posts: 40,
    progress: 0.74,
    delta: -2,
    status: 'ok',
    reach: 8_200_000,
    reachLabel: '8.2M',
    biggestReach: false,
  },
  {
    handle: '@demishassabis',
    name: 'Demis Hassabis',
    companyId: 'deepmind',
    companyName: 'Google DeepMind',
    score: 0,
    index: null,
    posts: 2,
    progress: 0,
    delta: null,
    status: 'not_enough_posts',
    reach: 1400,
    reachLabel: '1.4K',
    biggestReach: false,
  },
]

const fallbackMover: Mover = {
  companyId: 'anthropic',
  name: 'Anthropic',
  change: 18,
  period: 'week',
}

export const formatNumber = (n: number) => n.toLocaleString('en-US')

export function formatIndex(index: number) {
  return index.toFixed(1)
}

export function formatUpdated(updatedAt: string | null, now = Date.now()): string | null {
  if (!updatedAt) return null
  const then = Date.parse(updatedAt)
  if (Number.isNaN(then)) return null
  const minutes = Math.max(0, Math.round((now - then) / 60000))
  if (minutes < 1) return 'Updated just now'
  if (minutes === 1) return 'Updated 1 min ago'
  if (minutes < 60) return `Updated ${minutes} min ago`
  const hours = Math.max(1, Math.round(minutes / 60))
  if (hours < 48) return `Updated ${hours} hour${hours === 1 ? '' : 's'} ago`
  const days = Math.round(hours / 24)
  return `Updated ${days} days ago`
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function asNumber(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) return value
  if (typeof value === 'string' && value.trim() && Number.isFinite(Number(value))) {
    return Number(value)
  }
  return null
}

function asText(value: unknown, fallback = ''): string {
  if (typeof value !== 'string') return fallback
  const text = value.trim()
  return text || fallback
}

function companyIdFrom(value: unknown): CompanyId | null {
  if (typeof value !== 'string') return null
  return NAME_TO_ID[value.trim().toLowerCase()] ?? null
}

function normalizeCompany(raw: unknown): Company | null {
  if (!isRecord(raw)) return null
  const id = companyIdFrom(raw.id) ?? companyIdFrom(raw.name) ?? companyIdFrom(raw.company)
  if (!id) return null
  const defaults = DISPLAY[id]
  const posts = asNumber(raw.posts)
  if (posts === null) return null
  const indexField = asNumber(raw.index)
  const scoreField = asNumber(raw.score)
  let status: CompanyStatus = 'ok'
  let index: number | null = null
  if (raw.status === 'not_enough_posts') {
    status = 'not_enough_posts'
  } else if (indexField !== null) {
    index = indexField
  } else if (scoreField !== null && scoreField <= 10) {
    index = scoreField
  } else if (scoreField !== null) {
    status = 'pending'
  } else {
    return null
  }
  if (status !== 'ok') index = null
  const progressField = asNumber(raw.progress)
  const progress =
    status === 'ok' && index !== null
      ? Math.max(0, Math.min(1, progressField === null ? index / 10 : progressField > 1 && progressField <= 100 ? progressField / 100 : progressField))
      : 0
  const logoMode = raw.logoMode === 'image' || raw.logoMode === 'mask' ? raw.logoMode : defaults.logoMode
  const company: Company = {
    id,
    name: asText(raw.name, defaults.name),
    score: index ?? 0,
    posts,
    progress,
    accent: asText(raw.accent, asText(raw.color, defaults.accent)),
    logo: asText(raw.logo, defaults.logo),
    logoMode,
    index,
    delta: status === 'ok' ? asNumber(raw.delta) : null,
    status,
  }
  const logoColor = asText(raw.logoColor, defaults.logoColor ?? '')
  if (logoColor) company.logoColor = logoColor
  return company
}

export function normalizeCompanies(input: unknown): Company[] | null {
  if (!Array.isArray(input)) return null
  const companies = input.map((item) => normalizeCompany(item)).filter((item): item is Company => item !== null)
  if (companies.length === 0) return null
  return companies
}

export function normalizePosts(input: unknown): Post[] | null {
  if (!Array.isArray(input)) return null
  const posts: Post[] = []
  input.forEach((raw, index) => {
    if (!isRecord(raw)) return
    const companyId = companyIdFrom(raw.companyId) ?? companyIdFrom(raw.company) ?? companyIdFrom(raw.name)
    if (!companyId) return
    const text = asText(raw.text)
    if (!text) return
    const handle = asText(raw.handle, `@${companyId}`)
    let name = asText(raw.name)
    if (!name || NAME_TO_ID[name.toLowerCase()]) name = DISPLAY[companyId].name
    const url = asText(raw.url)
    const post: Post = {
      id: asText(raw.id, `p${index + 1}`),
      companyId,
      name,
      handle: handle.startsWith('@') ? handle : `@${handle}`,
      time: asText(raw.time),
      text,
      replies: asText(raw.replies, '0'),
      reposts: asText(raw.reposts, '0'),
      likes: asText(raw.likes, '0'),
      inlineHandle: raw.inlineHandle === true,
    }
    if (url) post.url = url
    posts.push(post)
  })
  return posts
}

export function normalizeLeaders(input: unknown): Leader[] {
  if (!Array.isArray(input)) return []
  const leaders: Leader[] = []
  input.forEach((raw) => {
    if (!isRecord(raw)) return
    const companyId = companyIdFrom(raw.companyId) ?? companyIdFrom(raw.companyName)
    if (!companyId) return
    const handle = asText(raw.handle)
    if (!handle) return
    const posts = asNumber(raw.posts)
    if (posts === null) return
    const status: CompanyStatus = raw.status === 'not_enough_posts' ? 'not_enough_posts' : raw.status === 'pending' ? 'pending' : 'ok'
    const index = status === 'ok' ? asNumber(raw.index) ?? asNumber(raw.score) : null
    const reach = asNumber(raw.reach) ?? 0
    leaders.push({
      handle: handle.startsWith('@') ? handle : `@${handle}`,
      name: asText(raw.name, handle),
      companyId,
      companyName: asText(raw.companyName, DISPLAY[companyId].name),
      score: index ?? 0,
      index,
      posts,
      progress: status === 'ok' && index !== null ? Math.max(0, Math.min(1, (asNumber(raw.progress) ?? index / 10))) : 0,
      delta: status === 'ok' ? asNumber(raw.delta) : null,
      status,
      reach,
      reachLabel: asText(raw.reachLabel, formatNumber(reach)),
      biggestReach: raw.biggestReach === true,
    })
  })
  return leaders
}

function countLabel(value: unknown): string {
  const number = asNumber(value)
  if (number === null) return asText(value, '0')
  const rounded = Math.max(0, Math.round(number))
  if (rounded < 1000) return String(rounded)
  const scaled = rounded < 1_000_000 ? rounded / 1000 : rounded / 1_000_000
  const suffix = rounded < 1_000_000 ? 'K' : 'M'
  return `${scaled.toFixed(1).replace(/\.0$/, '')}${suffix}`
}

export function normalizeTopPost(raw: unknown): TopPost | null {
  if (!isRecord(raw)) return null
  const companyId = companyIdFrom(raw.companyId) ?? companyIdFrom(raw.lab)
  if (!companyId) return null
  const text = asText(raw.text)
  const author = asText(raw.author, asText(raw.name))
  const handle = asText(raw.handle)
  if (!text || !author || !handle) return null
  const engagement = asNumber(raw.engagement)
  const url = asText(raw.url)
  const post: TopPost = {
    author,
    handle: handle.startsWith('@') ? handle : `@${handle}`,
    lab: asText(raw.lab, DISPLAY[companyId].name),
    companyId,
    text,
    likes: countLabel(raw.likes),
    reposts: countLabel(raw.reposts),
    replies: countLabel(raw.replies),
    engagement: engagement ?? 0,
    createdAt: asText(raw.createdAt),
    time: asText(raw.time),
  }
  if (url) post.url = url
  return post
}

function normalizeMover(raw: unknown): Mover | null {
  if (!isRecord(raw)) return null
  const companyId = companyIdFrom(raw.companyId) ?? companyIdFrom(raw.name)
  const change = asNumber(raw.change)
  if (!companyId || change === null) return null
  const period = raw.period === 'week' ? 'week' : 'today'
  return {
    companyId,
    name: asText(raw.name, DISPLAY[companyId].name),
    change,
    period,
  }
}

export async function fetchArenaData(): Promise<ArenaData> {
  try {
    const res = await fetch(GITHUB_DATA_URL, { next: { revalidate: REVALIDATE_SECONDS } })
    if (!res.ok) throw new Error(`Score file responded ${res.status}`)
    const data: unknown = await res.json()
    const record = isRecord(data) ? data : {}
    const companies = normalizeCompanies(record.companies)
    if (!companies) throw new Error('Score file is missing companies')
    const posts = normalizePosts(record.posts)
    return {
      companies,
      posts: posts ?? fallbackPosts,
      leaders: normalizeLeaders(record.leaders),
      usingFallback: false,
      updatedAt: asText(record.updatedAt) || null,
      mover: normalizeMover(record.mover),
      topPost: normalizeTopPost(record.topPost),
    }
  } catch (err) {
    console.error('Using saved arena scores', err)
    return {
      companies: fallbackCompanies,
      posts: fallbackPosts,
      leaders: fallbackLeaders,
      usingFallback: true,
      updatedAt: null,
      mover: fallbackMover,
      topPost: null,
    }
  }
}
