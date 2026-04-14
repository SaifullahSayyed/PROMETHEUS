import type { Metadata } from 'next'
import { Rajdhani, Share_Tech_Mono, Orbitron } from 'next/font/google'
import './globals.css'

const rajdhani = Rajdhani({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-rajdhani',
})

const shareTechMono = Share_Tech_Mono({
  subsets: ['latin'],
  weight: '400',
  variable: '--font-mono',
})

const orbitron = Orbitron({
  subsets: ['latin'],
  weight: ['400', '500', '700'],
  variable: '--font-orbitron',
})

export const metadata: Metadata = {
  title: 'PROMETHEUS — Adversarial Venture Engine',
  description: 'AI that builds a company, attacks it with 5 specialized critics, and ships the survivor to a live URL.',
  keywords: ['AI', 'startup', 'venture engine', 'adversarial', 'claude'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html
      lang="en"
      className={`${rajdhani.variable} ${shareTechMono.variable} ${orbitron.variable}`}
    >
      <body>{children}</body>
    </html>
  )
}
