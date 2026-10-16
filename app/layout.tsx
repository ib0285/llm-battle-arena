import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import type { ReactNode } from 'react'
import './globals.css'

const inter = Inter({ subsets: ['latin'], display: 'swap' })

const description = "Who's winning attention on X. Engagement per follower, rolling 7 days. Just for fun, not a measure of which AI is best."

const siteUrl = process.env.VERCEL_PROJECT_PRODUCTION_URL
  ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`
  : 'https://llm-battle-arena-liard.vercel.app'

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: 'LLM Battle Arena',
  description,
  openGraph: {
    title: 'LLM Battle Arena',
    description: "Who's winning attention on X · Engagement per follower, rolling 7 days",
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'LLM Battle Arena',
    description: "Who's winning attention on X · Engagement per follower, rolling 7 days",
  },
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
