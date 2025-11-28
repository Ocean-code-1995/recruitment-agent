import type { Metadata } from 'next'
import './globals.css'
import Navigation from '../components/Navigation'

export const metadata: Metadata = {
  title: 'ScionHire AI Labs - Recruitment Agent System',
  description: 'AI-powered recruitment agent system with candidate portal, HR portal, and agent dashboard',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <Navigation />
        {children}
      </body>
    </html>
  )
}

