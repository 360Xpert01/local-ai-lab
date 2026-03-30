import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Local AI Lab',
  description: 'Dynamic Model-Agnostic AI Development Environment',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans">{children}</body>
    </html>
  )
}
