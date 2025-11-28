/**
 * SDK Configuration
 * Handles base URL configuration for all API clients
 */

export function getBaseUrl(service: 'supervisor' | 'database' | 'cv' | 'voice-screener'): string {
  // Check for environment-specific URLs first
  const envVar = {
    supervisor: process.env.NEXT_PUBLIC_SUPERVISOR_API_URL,
    database: process.env.NEXT_PUBLIC_DATABASE_API_URL,
    cv: process.env.NEXT_PUBLIC_CV_UPLOAD_API_URL,
    'voice-screener': process.env.NEXT_PUBLIC_VOICE_SCREENER_API_URL,
  }[service];

  if (envVar) {
    return envVar;
  }

  // Default to localhost with standard ports
  const defaultPort = {
    supervisor: '8080',
    database: '8080',
    cv: '8080',
    'voice-screener': '8080',
  }[service];

  const basePath = {
    supervisor: '/api/v1/supervisor',
    database: '/api/v1/db',
    cv: '/api/v1/cv',
    'voice-screener': '/api/v1/voice-screener',
  }[service];

  // In browser, use relative URLs or full URL based on environment
  if (typeof window !== 'undefined') {
    const host = window.location.hostname === 'localhost' 
      ? `http://localhost:${defaultPort}`
      : window.location.origin;
    return `${host}${basePath}`;
  }

  // Server-side fallback
  return `http://localhost:${defaultPort}${basePath}`;
}

