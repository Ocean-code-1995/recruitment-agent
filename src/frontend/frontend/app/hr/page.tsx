'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { DatabaseClient, SupervisorClient, VoiceScreeningClient } from '@/lib/sdk'

interface Candidate {
  id: string
  name: string
  email: string
  phone?: string
  status: string
  appliedAt: string
  position?: string
  skills?: string[]
  experience?: string
  education?: string
  hasVoiceScreening?: boolean
  authCode?: string
}

export default function HRPortal() {
  const router = useRouter()
  const [dbClient] = useState(() => new DatabaseClient())
  const [supervisorClient] = useState(() => new SupervisorClient())
  const [voiceScreeningClient] = useState(() => new VoiceScreeningClient())
  const [connected, setConnected] = useState(false)
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null)

  useEffect(() => {
    const initClients = async () => {
      try {
        const [dbHealthy, supervisorHealthy] = await Promise.all([
          dbClient.health(),
          supervisorClient.health()
        ])
        setConnected(dbHealthy && supervisorHealthy)
        
        // Load candidates from database
        if (dbHealthy) {
          loadCandidates()
        }
      } catch (error) {
        console.error('Failed to check API health:', error)
        setConnected(false)
      }
    }
    initClients()
  }, [dbClient, supervisorClient])

  const loadCandidates = async () => {
    try {
      setLoading(true)
      // Load candidates with relations to check for voice screening
      const response = await dbClient.getCandidates(undefined, 100, 0, true)
      if (response.success) {
        // Transform database response to Candidate format
        const transformedCandidates: Candidate[] = response.data.map((c: any) => ({
          id: c.id,
          name: c.full_name || 'Unknown',
          email: c.email || '',
          phone: c.phone_number || '',
          status: c.status || 'unknown',
          appliedAt: c.created_at || new Date().toISOString(),
          position: 'AI Engineer', // Default position
          hasVoiceScreening: c.voice_screening_results && c.voice_screening_results.length > 0,
          authCode: c.auth_code || undefined,
        }))
        setCandidates(transformedCandidates)
      }
    } catch (error) {
      console.error('Failed to load candidates:', error)
    } finally {
      setLoading(false)
    }
  }

  const triggerVoiceScreening = async (candidate: Candidate) => {
    if (!connected) return
    setLoading(true)
    try {
      // Create voice screening session using SDK
      const sessionResponse = await voiceScreeningClient.createSession(candidate.id)
      
      // Use supervisor agent to notify about voice screening
      const supervisorResponse = await supervisorClient.chat(
        `Voice screening session created for candidate ${candidate.name} (${candidate.email}). Session ID: ${sessionResponse.session_id}. Please proceed with the voice screening process.`
      )
      
      const tokenInfo = supervisorResponse.token_count 
        ? `\n\n📊 Token usage: ${supervisorResponse.token_count.toLocaleString()} tokens`
        : ''
      
      const authCodeInfo = candidate.authCode 
        ? `\n\n🔐 Authentication Code: ${candidate.authCode}\n(Candidate should use this code to access voice screening)`
        : ''
      
      const voiceScreeningUrl = `http://localhost:8502?candidate_id=${candidate.id}`
      
      alert(`✅ Voice screening session created for ${candidate.name}!\n\nSession ID: ${sessionResponse.session_id}${authCodeInfo}\n\nVoice Screening URL: ${voiceScreeningUrl}\n\n${supervisorResponse.content}${tokenInfo}\n\nYou can now direct the candidate to complete the voice screening.`)
      
      // Reload candidates to get updated status
      await loadCandidates()
    } catch (error: any) {
      alert(`Failed to trigger voice screening: ${error.message || 'Unknown error'}`)
      console.error('Failed to trigger voice screening:', error)
    } finally {
      setLoading(false)
    }
  }

  const scheduleInterview = async (candidate: Candidate) => {
    if (!connected) return
    setLoading(true)
    try {
      // Use supervisor agent to schedule interview
      const response = await supervisorClient.chat(
        `Please schedule an interview for candidate ${candidate.name} (${candidate.email})`
      )
      const tokenInfo = response.token_count 
        ? `\n\n📊 Token usage: ${response.token_count.toLocaleString()} tokens`
        : ''
      alert(`Interview scheduling initiated for ${candidate.name}\n\nAgent response: ${response.content}${tokenInfo}`)
      // Reload candidates to get updated status
      await loadCandidates()
    } catch (error: any) {
      alert(`Failed to schedule interview: ${error.message || 'Unknown error'}`)
      console.error('Failed to schedule interview:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'applied': return '#f59e0b'
      case 'cv_screened': return '#3b82f6'
      case 'cv_passed': return '#10b981'
      case 'cv_rejected': return '#ef4444'
      case 'voice_invitation_sent': return '#8b5cf6'
      case 'voice_done': return '#8b5cf6'
      case 'voice_passed': return '#10b981'
      case 'voice_rejected': return '#ef4444'
      case 'interview_scheduled': return '#10b981'
      case 'decision_made': return '#6366f1'
      default: return '#6b7280'
    }
  }

  return (
    <main style={{
      minHeight: '100vh',
      padding: '2rem',
      background: '#f9fafb',
    }}>
      <div style={{
        maxWidth: '1400px',
        margin: '0 auto',
      }}>
        <div style={{
          background: 'white',
          borderRadius: '16px',
          padding: '2rem',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          marginBottom: '2rem',
        }}>
          <h1 style={{
            fontSize: '2.5rem',
            fontWeight: 'bold',
            color: '#1f2937',
            marginBottom: '0.5rem',
          }}>
            🧑‍💼 HR Portal
          </h1>
          <p style={{
            fontSize: '1.125rem',
            color: '#6b7280',
          }}>
            Review shortlisted candidates, trigger voice screenings, and schedule interviews
          </p>
        </div>

        {!connected && (
          <div style={{
            padding: '1rem',
            background: '#fee2e2',
            borderRadius: '8px',
            marginBottom: '2rem',
            color: '#991b1b',
          }}>
            ⚠️ Backend not connected. Some features may not work.
          </div>
        )}

        {/* Candidates Table */}
        <div style={{
          background: 'white',
          borderRadius: '16px',
          padding: '2rem',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        }}>
          <h2 style={{
            fontSize: '1.5rem',
            fontWeight: '600',
            marginBottom: '1.5rem',
            color: '#1f2937',
          }}>
            📋 Candidate List
          </h2>

          <div style={{
            overflowX: 'auto',
          }}>
            <table style={{
              width: '100%',
              borderCollapse: 'collapse',
            }}>
              <thead>
                <tr style={{
                  borderBottom: '2px solid #e5e7eb',
                }}>
                  <th style={{
                    padding: '1rem',
                    textAlign: 'left',
                    fontWeight: '600',
                    color: '#374151',
                  }}>Name</th>
                  <th style={{
                    padding: '1rem',
                    textAlign: 'left',
                    fontWeight: '600',
                    color: '#374151',
                  }}>Email</th>
                  <th style={{
                    padding: '1rem',
                    textAlign: 'left',
                    fontWeight: '600',
                    color: '#374151',
                  }}>Status</th>
                  <th style={{
                    padding: '1rem',
                    textAlign: 'left',
                    fontWeight: '600',
                    color: '#374151',
                  }}>Applied</th>
                  <th style={{
                    padding: '1rem',
                    textAlign: 'left',
                    fontWeight: '600',
                    color: '#374151',
                  }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {candidates.map((candidate) => (
                  <tr
                    key={candidate.id}
                    style={{
                      borderBottom: '1px solid #e5e7eb',
                      cursor: 'pointer',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = '#f9fafb'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'white'
                    }}
                    onClick={() => setSelectedCandidate(candidate)}
                  >
                    <td style={{ padding: '1rem', color: '#1f2937' }}>{candidate.name}</td>
                    <td style={{ padding: '1rem', color: '#6b7280' }}>{candidate.email}</td>
                    <td style={{ padding: '1rem' }}>
                      <span style={{
                        padding: '0.25rem 0.75rem',
                        borderRadius: '12px',
                        fontSize: '0.875rem',
                        fontWeight: '500',
                        background: getStatusColor(candidate.status) + '20',
                        color: getStatusColor(candidate.status),
                      }}>
                        {candidate.status}
                      </span>
                    </td>
                    <td style={{ padding: '1rem', color: '#6b7280' }}>
                      {new Date(candidate.appliedAt).toLocaleDateString()}
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <div style={{
                        display: 'flex',
                        gap: '0.5rem',
                      }}>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            router.push(`/dashboard/${candidate.id}`)
                          }}
                          style={{
                            padding: '0.5rem 1rem',
                            background: '#2563eb',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            fontSize: '0.875rem',
                            fontWeight: '500',
                            cursor: 'pointer',
                          }}
                        >
                          📊 View Dashboard
                        </button>
                        {/* Show voice screening button if candidate hasn't done voice screening yet */}
                        {!candidate.hasVoiceScreening && (
                          candidate.status === 'cv_screened' || 
                          candidate.status === 'cv_passed' || 
                          candidate.status === 'applied'
                        ) && (
                          <>
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                triggerVoiceScreening(candidate)
                              }}
                              disabled={loading}
                              style={{
                                padding: '0.5rem 1rem',
                                background: '#8b5cf6',
                                color: 'white',
                                border: 'none',
                                borderRadius: '6px',
                                fontSize: '0.875rem',
                                fontWeight: '500',
                                cursor: loading ? 'not-allowed' : 'pointer',
                              }}
                              title="Create voice screening session"
                            >
                              🎙️ Create Session
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                // Open voice screening UI in new tab with candidate ID
                                const voiceScreeningUrl = `http://localhost:8502?candidate_id=${candidate.id}`
                                window.open(voiceScreeningUrl, '_blank')
                              }}
                              style={{
                                padding: '0.5rem 1rem',
                                background: '#10b981',
                                color: 'white',
                                border: 'none',
                                borderRadius: '6px',
                                fontSize: '0.875rem',
                                fontWeight: '500',
                                cursor: 'pointer',
                              }}
                              title="Open voice screening interface"
                            >
                              🎤 Start Interview
                            </button>
                          </>
                        )}
                        {(candidate.status === 'voice_passed' || candidate.status === 'voice_done') && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              scheduleInterview(candidate)
                            }}
                            disabled={loading}
                            style={{
                              padding: '0.5rem 1rem',
                              background: '#10b981',
                              color: 'white',
                              border: 'none',
                              borderRadius: '6px',
                              fontSize: '0.875rem',
                              fontWeight: '500',
                              cursor: loading ? 'not-allowed' : 'pointer',
                            }}
                          >
                            📅 Schedule
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {candidates.length === 0 && (
            <div style={{
              padding: '3rem',
              textAlign: 'center',
              color: '#6b7280',
            }}>
              No candidates found. Applications will appear here once submitted.
            </div>
          )}
        </div>

        {/* Candidate Details Modal */}
        {selectedCandidate && (
          <div
            onClick={() => setSelectedCandidate(null)}
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'rgba(0, 0, 0, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1000,
            }}
          >
            <div
              onClick={(e) => e.stopPropagation()}
              style={{
                background: 'white',
                borderRadius: '16px',
                padding: '2rem',
                maxWidth: '600px',
                width: '90%',
                maxHeight: '80vh',
                overflow: 'auto',
              }}
            >
              <h2 style={{
                fontSize: '1.5rem',
                fontWeight: '600',
                marginBottom: '1rem',
                color: '#1f2937',
              }}>
                Candidate Details
              </h2>
              <div style={{
                marginBottom: '1rem',
              }}>
                <p><strong>Name:</strong> {selectedCandidate.name}</p>
                <p><strong>Email:</strong> {selectedCandidate.email}</p>
                <p><strong>Phone:</strong> {selectedCandidate.phone || 'N/A'}</p>
                <p><strong>Position:</strong> {selectedCandidate.position || 'AI Engineer'}</p>
                <p><strong>Status:</strong> {selectedCandidate.status}</p>
                <p><strong>Applied:</strong> {new Date(selectedCandidate.appliedAt).toLocaleString()}</p>
                {selectedCandidate.hasVoiceScreening !== undefined && (
                  <p><strong>Voice Screening:</strong> {selectedCandidate.hasVoiceScreening ? '✅ Completed' : '❌ Not completed'}</p>
                )}
                {selectedCandidate.authCode && (
                  <p><strong>Authentication Code:</strong> <code style={{ background: '#f3f4f6', padding: '0.25rem 0.5rem', borderRadius: '4px' }}>{selectedCandidate.authCode}</code></p>
                )}
                <div style={{ marginTop: '1rem', padding: '1rem', background: '#f3f4f6', borderRadius: '8px' }}>
                  <p style={{ margin: '0 0 0.5rem 0', fontWeight: '600' }}>🎤 Voice Screening Access:</p>
                  <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem' }}>
                    <strong>URL:</strong> <a href={`http://localhost:8502?candidate_id=${selectedCandidate.id}`} target="_blank" rel="noopener noreferrer" style={{ color: '#2563eb' }}>
                      http://localhost:8502?candidate_id={selectedCandidate.id}
                    </a>
                  </p>
                  {selectedCandidate.authCode && (
                    <p style={{ margin: 0, fontSize: '0.875rem' }}>
                      <strong>Auth Code:</strong> <code style={{ background: 'white', padding: '0.25rem 0.5rem', borderRadius: '4px' }}>{selectedCandidate.authCode}</code>
                    </p>
                  )}
                </div>
              </div>
              <button
                onClick={() => {
                  setSelectedCandidate(null)
                  router.push(`/dashboard/${selectedCandidate.id}`)
                }}
                style={{
                  padding: '0.75rem 1.5rem',
                  background: '#2563eb',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  marginRight: '0.5rem',
                }}
              >
                View Agent Dashboard
              </button>
              <button
                onClick={() => setSelectedCandidate(null)}
                style={{
                  padding: '0.75rem 1.5rem',
                  background: '#6b7280',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                }}
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}

