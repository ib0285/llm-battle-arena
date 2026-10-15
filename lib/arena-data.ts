// Scores are loaded on the server from the GitHub file, then passed into
// the page. The browser does not fetch this itself.

const GITHUB_DATA_URL =
  process.env.ARENA_SCORES_URL ||
  'https://raw.githubusercontent.com/ib0285/llm-battle-arena/main/scores.json'

export const REVALIDATE_SECONDS = 300

export type CompanyId = 'xai' | 'openai' | 'meta' | 'anthropic' | 'deepmind'

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
  badge?: string
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
}

export type ArenaData = {
  companies: Company[]
  posts: Post[]
  usingFallback: boolean
}

type CompanyDefaults = Omit<Company, 'score' | 'posts' | 'progress'>

const DISPLAY: Record<CompanyId, CompanyDefaults> = {
  xai: {
    id: 'xai',
    name: 'xAI',
    accent: '#e9b949',
    logo: '/logos/xai.svg',
    logoMode: 'mask',
    logoColor: 'linear-gradient(160deg,#ffe08a,#d9a032)',
    badge: '+10% (It’s his app)',
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

// Full saved copy of the original scoreboard. Used only when the live file
// cannot be read. Every company is included.
const fallbackCompanies: Company[] = [
  {
    id: 'xai',
    name: 'xAI',
    score: 128754,
    posts: 2341,
    progress: 0.82,
    accent: '#e9b949',
    logo: '/logos/xai.svg',
    logoMode: 'mask',
    logoColor: 'linear-gradient(160deg,#ffe08a,#d9a032)',
    badge: '+10% (It’s his app)',
  },
  {
    id: 'openai',
    name: 'OpenAI',
    score: 96432,
    posts: 1892,
    progress: 0.83,
    accent: '#34d399',
    logo: '/logos/openai.svg',
    logoMode: 'mask',
    logoColor: '#ffffff',
  },
  {
    id: 'meta',
    name: 'Meta',
    score: 45283,
    posts: 983,
    progress: 0.85,
    accent: '#3b9cf6',
    logo: '/logos/meta.svg',
    logoMode: 'image',
  },
  {
    id: 'anthropic',
    name: 'Anthropic',
    score: 71309,
    posts: 1456,
    progress: 0.85,
    accent: '#9f6bf5',
    logo: '/logos/anthropic.svg',
    logoMode: 'mask',
    logoColor: 'linear-gradient(160deg,#c4a1ff,#8b5cf6)',
  },
  {
    id: 'deepmind',
    name: 'Google DeepMind',
    score: 58667,
    posts: 1102,
    progress: 0.8,
    accent: '#3b82f6',
    logo: '/logos/deepmind.svg',
    logoMode: 'mask',
    logoColor: 'linear-gradient(135deg,#4f8df7 0%,#4f8df7 45%,#f7c544 55%,#f7c544 100%)',
  },
]

const fallbackPosts: Post[] = [
  {
    id: 'p1',
    companyId: 'xai',
    name: 'Elon Musk',
    handle: '@elonmusk',
    time: '3m',
    text: 'The whole world will watch this',
    replies: '4.8K',
    reposts: '9.2K',
    likes: '61K',
    inlineHandle: true,
  },
]

export const formatNumber = (n: number) => n.toLocaleString('en-US')

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

function normalizeCompany(raw: unknown): Omit<Company, 'progress'> & { progress: number | null } | null {
  if (!isRecord(raw)) return null
  const id = companyIdFrom(raw.id) ?? companyIdFrom(raw.name) ?? companyIdFrom(raw.company)
  if (!id) return null
  const defaults = DISPLAY[id]
  const score = asNumber(raw.score)
  const posts = asNumber(raw.posts)
  if (score === null || posts === null) return null
  let progress = asNumber(raw.progress)
  if (progress !== null && progress > 1 && progress <= 100) progress = progress / 100
  const logoMode = raw.logoMode === 'image' || raw.logoMode === 'mask' ? raw.logoMode : defaults.logoMode
  const company: Omit<Company, 'progress'> & { progress: number | null } = {
    id,
    name: asText(raw.name, defaults.name),
    score,
    posts,
    progress,
    accent: asText(raw.accent, asText(raw.color, defaults.accent)),
    logo: asText(raw.logo, defaults.logo),
    logoMode,
  }
  const logoColor = asText(raw.logoColor, defaults.logoColor ?? '')
  if (logoColor) company.logoColor = logoColor
  const badge = raw.badge === undefined ? defaults.badge : asText(raw.badge)
  if (badge) company.badge = badge
  return company
}

function withProgress(companies: Array<Omit<Company, 'progress'> & { progress: number | null }>): Company[] {
  const highest = Math.max(...companies.map((company) => company.score), 1)
  return companies.map((company) => {
    const authored = company.progress
    const progress =
      authored === null
        ? Math.round(Math.max(0.05, Math.min(1, company.score / highest)) * 100) / 100
        : Math.max(0, Math.min(1, authored))
    return { ...company, progress }
  })
}

export function normalizeCompanies(input: unknown): Company[] | null {
  if (!Array.isArray(input)) return null
  const companies = input
    .map((item) => normalizeCompany(item))
    .filter((item): item is NonNullable<typeof item> => item !== null)
  if (companies.length === 0) return null
  return withProgress(companies)
}

export function normalizePosts(input: unknown): Post[] | null {
  if (!Array.isArray(input)) return null
  const posts: Post[] = []
  input.forEach((raw, index) => {
    if (!isRecord(raw)) return
    const companyId =
      companyIdFrom(raw.companyId) ?? companyIdFrom(raw.company) ?? companyIdFrom(raw.name)
    if (!companyId) return
    const text = asText(raw.text)
    if (!text) return
    const handle = asText(raw.handle, `@${companyId}`)
    let name = asText(raw.name)
    if (!name || NAME_TO_ID[name.toLowerCase()]) name = DISPLAY[companyId].name
    posts.push({
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
    })
  })
  return posts
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
      usingFallback: false,
    }
  } catch (err) {
    console.error('Using saved arena scores', err)
    return {
      companies: fallbackCompanies,
      posts: fallbackPosts,
      usingFallback: true,
    }
  }
}
