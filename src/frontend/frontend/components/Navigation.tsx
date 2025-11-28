'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

export default function Navigation() {
  const pathname = usePathname()

  const navItems = [
    { href: '/', label: '🧍 Candidate Portal', icon: '👤' },
    { href: '/hr', label: '🧑‍💼 HR Portal', icon: '💼' },
    { href: '/chat', label: '🤖 Supervisor Chat', icon: '💬' },
  ]

  return (
    <nav style={{
      background: 'white',
      borderBottom: '2px solid #e5e7eb',
      padding: '1rem 2rem',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    }}>
      <div style={{
        maxWidth: '1400px',
        margin: '0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <h1 style={{
            fontSize: '1.5rem',
            fontWeight: 'bold',
            color: '#2563eb',
            margin: 0,
          }}>
            🤖 ScionHire AI Labs
          </h1>
        </div>
        
        <div style={{
          display: 'flex',
          gap: '0.5rem',
        }}>
          {navItems.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                style={{
                  padding: '0.75rem 1.5rem',
                  borderRadius: '8px',
                  textDecoration: 'none',
                  fontWeight: '500',
                  fontSize: '1rem',
                  transition: 'all 0.2s',
                  background: isActive ? '#2563eb' : 'transparent',
                  color: isActive ? 'white' : '#374151',
                  border: isActive ? 'none' : '1px solid #e5e7eb',
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = '#f3f4f6'
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = 'transparent'
                  }
                }}
              >
                {item.label}
              </Link>
            )
          })}
        </div>
      </div>
    </nav>
  )
}

