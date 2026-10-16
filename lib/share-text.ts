const SITE = 'https://llm-battle-arena-liard.vercel.app'

export function entityLink(tab: 'companies' | 'leaders', id: string) {
  const url = new URL(SITE)
  if (tab === 'leaders') url.searchParams.set('tab', 'leaders')
  url.searchParams.set('open', id)
  return url.toString()
}

export function shareText({
  name,
  place,
  reactionsLabel,
  biggestReach,
  link,
}: {
  name: string
  place: number | null
  reactionsLabel: string
  biggestReach: boolean
  link: string
}) {
  if (place === null) {
    return `${name}: not enough posts for a score this week. Who's #1? ${link} via LLM Battle Arena`
  }
  if (biggestReach) {
    return `${name}: biggest reach on X this week (${reactionsLabel} reactions), but #${place} per follower. Who's #1? ${link} via LLM Battle Arena`
  }
  return `${name}: #${place} per follower this week, ${reactionsLabel} total reactions. Who's #1? ${link} via LLM Battle Arena`
}

export function intentUrl(text: string) {
  return `https://x.com/intent/tweet?text=${encodeURIComponent(text)}`
}
