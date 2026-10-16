import { leaderKey, type Company, type Leader } from '@/lib/arena-data'

export function resolveOpen(
  tabParam: string | undefined,
  openParam: string | undefined,
  companies: Company[],
  leaders: Leader[],
) {
  const open = leaderKey(openParam || '')
  const leaderMatch = Boolean(open) && leaders.some((person) => leaderKey(person.handle) === open)
  const companyMatch = Boolean(open) && companies.some((company) => company.id === open)
  let tab: 'companies' | 'leaders' = tabParam === 'leaders' ? 'leaders' : 'companies'
  if (leaderMatch) tab = 'leaders'
  else if (companyMatch) tab = 'companies'
  return { tab, openId: leaderMatch || companyMatch ? open : null }
}
