'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { DatabaseClient } from '@/lib/sdk'

interface Candidate {
  id: string
  name: string
  email: string
  phone?: string
  status: string
  appliedAt: string
  position?: string
  plan?: PlanStep[]
  reasoningLog?: ReasoningLog[]
  cvScreeningResults?: any[]
  voiceScreeningResults?: any[]
  interviewScheduling?: any[]
  finalDecision?: any
}

interface PlanStep {
  id: string
  step: string
  status: 'completed' | 'in_progress' | 'pending'
  timestamp?: string
}

interface ReasoningLog {
  timestamp: string
  message: string
  type?: 'info' | 'success' | 'warning' | 'error'
}

export default function CandidateDashboard() {
  const params = useParams()
  const router = useRouter()
  const candidateId = params.candidateId as string
  const [dbClient] = useState(() => new DatabaseClient())
  
  const [candidate, setCandidate] = useState<Candidate | null>(null)
  const [loading, setLoading] = useState(true)
  const [expandedStep, setExpandedStep] = useState<string | null>(null)
  const [hoveredStep, setHoveredStep] = useState<string | null>(null)

  useEffect(() => {
    const loadCandidate = async () => {
      try {
        setLoading(true)
        const response = await dbClient.getCandidate(candidateId, true)
        
        if (!response.success || !response.data) {
          router.push('/hr')
          return
        }

        const c = response.data
        
        // Build plan steps from candidate data
        const plan: PlanStep[] = []
        
        // Step 1: CV Screening
        if (c.cv_screening_results && c.cv_screening_results.length > 0) {
          plan.push({
            id: '1',
            step: 'Screen CVs',
            status: 'completed',
            timestamp: c.cv_screening_results[0].timestamp 
              ? new Date(c.cv_screening_results[0].timestamp).toLocaleTimeString()
              : undefined,
          })
        } else {
          plan.push({
            id: '1',
            step: 'Screen CVs',
            status: c.status === 'applied' ? 'in_progress' : 'pending',
          })
        }

        // Step 2: Voice Screening
        if (c.voice_screening_results && c.voice_screening_results.length > 0) {
          plan.push({
            id: '2',
            step: 'Conduct voice screening',
            status: 'completed',
            timestamp: c.voice_screening_results[0].timestamp
              ? new Date(c.voice_screening_results[0].timestamp).toLocaleTimeString()
              : undefined,
          })
        } else if (c.status === 'cv_passed' || c.status === 'cv_screened') {
          plan.push({
            id: '2',
            step: 'Conduct voice screening',
            status: 'pending',
          })
        }

        // Step 3: Interview Scheduling
        if (c.interview_scheduling && c.interview_scheduling.length > 0) {
          plan.push({
            id: '3',
            step: 'Schedule HR interview',
            status: 'completed',
            timestamp: c.interview_scheduling[0].timestamp
              ? new Date(c.interview_scheduling[0].timestamp).toLocaleTimeString()
              : undefined,
          })
        } else if (c.status === 'voice_passed' || c.status === 'voice_done') {
          plan.push({
            id: '3',
            step: 'Schedule HR interview',
            status: 'pending',
          })
        }

        // Step 4: Final Decision
        if (c.final_decision) {
          plan.push({
            id: '4',
            step: 'Final decision',
            status: 'completed',
            timestamp: c.final_decision.timestamp
              ? new Date(c.final_decision.timestamp).toLocaleTimeString()
              : undefined,
          })
        } else if (c.status === 'interview_scheduled') {
          plan.push({
            id: '4',
            step: 'Final decision',
            status: 'pending',
          })
        }

        // Build reasoning log from screening results
        const reasoningLog: ReasoningLog[] = []
        
        if (c.cv_screening_results && c.cv_screening_results.length > 0) {
          const cvResult = c.cv_screening_results[0]
          reasoningLog.push({
            timestamp: cvResult.timestamp 
              ? new Date(cvResult.timestamp).toLocaleTimeString()
              : new Date().toLocaleTimeString(),
            message: `CV Screening completed. Overall fit score: ${((cvResult.overall_fit_score || 0) * 10).toFixed(1)}/10. ${cvResult.llm_feedback || ''}`,
            type: (cvResult.overall_fit_score || 0) > 0.7 ? 'success' : 'info',
          })
        }

        if (c.voice_screening_results && c.voice_screening_results.length > 0) {
          const voiceResult = c.voice_screening_results[0]
          reasoningLog.push({
            timestamp: voiceResult.timestamp
              ? new Date(voiceResult.timestamp).toLocaleTimeString()
              : new Date().toLocaleTimeString(),
            message: `Voice screening completed. Communication score: ${((voiceResult.communication_score || 0) * 10).toFixed(1)}/10. ${voiceResult.llm_summary || ''}`,
            type: 'success',
          })
        }

        const transformedCandidate: Candidate = {
          id: c.id,
          name: c.full_name || 'Unknown',
          email: c.email || '',
          phone: c.phone_number || '',
          status: c.status || 'unknown',
          appliedAt: c.created_at || new Date().toISOString(),
          position: 'AI Engineer',
          plan,
          reasoningLog,
          cvScreeningResults: c.cv_screening_results,
          voiceScreeningResults: c.voice_screening_results,
          interviewScheduling: c.interview_scheduling,
          finalDecision: c.final_decision,
        }

        setCandidate(transformedCandidate)
      } catch (error) {
        console.error('Failed to load candidate:', error)
        router.push('/hr')
      } finally {
        setLoading(false)
      }
    }

    if (candidateId) {
      loadCandidate()
    }
  }, [candidateId, router, dbClient])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return '✅'
      case 'in_progress': return '🔄'
      case 'pending': return '⬜'
      default: return '⬜'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#10b981'
      case 'in_progress': return '#3b82f6'
      case 'pending': return '#6b7280'
      default: return '#6b7280'
    }
  }

  const getLogTypeColor = (type?: string) => {
    switch (type) {
      case 'success': return '#10b981'
      case 'error': return '#ef4444'
      case 'warning': return '#f59e0b'
      default: return '#3b82f6'
    }
  }

  const getStepDetails = (stepName: string, candidate: Candidate) => {
    const details: Record<string, { description: string; actions?: string[] }> = {
      'Screen CVs': {
        description: `The agent analyzed ${candidate.name}'s CV and evaluated their qualifications against the job requirements.`,
        actions: [
          'Extracted skills and experience from CV',
          'Scored candidate against job requirements',
          'Identified key strengths and potential gaps',
        ],
      },
      'Invite for voice screening': {
        description: `An invitation email was sent to ${candidate.email} to schedule a voice screening interview.`,
        actions: [
          'Generated personalized invitation email',
          'Sent email via Gmail integration',
          'Awaiting candidate response',
        ],
      },
      'Conduct voice screening': {
        description: `The voice screening interview is being conducted with ${candidate.name} to assess communication skills and technical knowledge.`,
        actions: [
          'Initiated automated voice call',
          'Conducted structured interview',
          'Analyzing responses and generating evaluation',
        ],
      },
      'Schedule HR interview': {
        description: `Based on the voice screening results, the agent is scheduling a final HR interview with ${candidate.name}.`,
        actions: [
          'Checked HR calendar availability',
          'Proposed interview time slots',
          'Sending calendar invitation',
        ],
      },
      'Await HR decision': {
        description: `The final decision is pending HR review. All screening stages have been completed for ${candidate.name}.`,
        actions: [
          'Compiled candidate evaluation report',
          'Submitted to HR for final review',
          'Awaiting hiring decision',
        ],
      },
    }
    return details[stepName] || { description: `Processing step: ${stepName}` }
  }

  if (loading || !candidate) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#f9fafb',
      }}>
        <div style={{
          textAlign: 'center',
        }}>
          <p style={{
            fontSize: '1.125rem',
            color: '#6b7280',
          }}>Loading candidate data...</p>
        </div>
      </div>
    )
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
        {/* Header */}
        <div style={{
          background: 'white',
          borderRadius: '16px',
          padding: '2rem',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          marginBottom: '2rem',
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <div>
              <h1 style={{
                fontSize: '2.5rem',
                fontWeight: 'bold',
                color: '#1f2937',
                marginBottom: '0.5rem',
              }}>
                🧠 Agent Dashboard
              </h1>
              <p style={{
                fontSize: '1.125rem',
                color: '#6b7280',
              }}>
                Managing application for <strong>{candidate.name}</strong> ({candidate.email})
              </p>
            </div>
            <button
              onClick={() => router.push('/hr')}
              style={{
                padding: '0.75rem 1.5rem',
                background: '#6b7280',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: '500',
              }}
            >
              ← Back to HR Portal
            </button>
          </div>
        </div>


        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '2rem',
          marginBottom: '2rem',
        }}>
          {/* Agent Plan Viewer */}
          <div style={{
            background: 'white',
            borderRadius: '16px',
            padding: '2rem',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1.5rem',
            }}>
              <h2 style={{
                fontSize: '1.5rem',
                fontWeight: '600',
                color: '#1f2937',
                margin: 0,
              }}>
                🗺️ Live Plan Progress
              </h2>
              <div style={{
                padding: '0.5rem 1rem',
                background: '#f3f4f6',
                borderRadius: '20px',
                fontSize: '0.875rem',
                color: '#6b7280',
              }}>
                {candidate.plan?.filter(s => s.status === 'completed').length || 0} / {candidate.plan?.length || 0} completed
              </div>
            </div>

            {/* Progress Bar */}
            <div style={{
              marginBottom: '2rem',
            }}>
              <div style={{
                width: '100%',
                height: '8px',
                background: '#e5e7eb',
                borderRadius: '4px',
                overflow: 'hidden',
                position: 'relative',
              }}>
                <div style={{
                  width: `${((candidate.plan?.filter(s => s.status === 'completed').length || 0) / (candidate.plan?.length || 1)) * 100}%`,
                  height: '100%',
                  background: 'linear-gradient(90deg, #10b981 0%, #3b82f6 100%)',
                  borderRadius: '4px',
                  transition: 'width 0.3s ease',
                }} />
              </div>
            </div>

            {/* Interactive Timeline */}
            <div style={{
              position: 'relative',
              paddingLeft: '2rem',
            }}>
              {/* Vertical line */}
              <div style={{
                position: 'absolute',
                left: '1.5rem',
                top: 0,
                bottom: 0,
                width: '2px',
                background: 'linear-gradient(to bottom, #10b981 0%, #3b82f6 50%, #e5e7eb 50%)',
                zIndex: 0,
              }} />

              <div style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '1.5rem',
                position: 'relative',
                zIndex: 1,
              }}>
                {candidate.plan?.map((step, index) => {
                  const isExpanded = expandedStep === step.id
                  const isHovered = hoveredStep === step.id
                  const stepDetails = getStepDetails(step.step, candidate)
                  
                  return (
                    <div
                      key={step.id}
                      onClick={() => setExpandedStep(isExpanded ? null : step.id)}
                      onMouseEnter={() => setHoveredStep(step.id)}
                      onMouseLeave={() => setHoveredStep(null)}
                      style={{
                        position: 'relative',
                        padding: '1.25rem',
                        background: isHovered 
                          ? (step.status === 'completed' ? '#d1fae5' : step.status === 'in_progress' ? '#dbeafe' : '#f9fafb')
                          : '#f9fafb',
                        borderRadius: '12px',
                        border: `2px solid ${isHovered ? getStatusColor(step.status) : '#e5e7eb'}`,
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        transform: isHovered ? 'translateX(4px)' : 'translateX(0)',
                        boxShadow: isHovered ? '0 4px 12px rgba(0, 0, 0, 0.1)' : 'none',
                      }}
                    >
                      {/* Step indicator */}
                      <div style={{
                        position: 'absolute',
                        left: '-2.5rem',
                        top: '1.5rem',
                        width: '2rem',
                        height: '2rem',
                        borderRadius: '50%',
                        background: step.status === 'completed' 
                          ? '#10b981' 
                          : step.status === 'in_progress' 
                          ? '#3b82f6' 
                          : '#e5e7eb',
                        border: '3px solid white',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.875rem',
                        fontWeight: '600',
                        color: step.status === 'pending' ? '#9ca3af' : 'white',
                        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
                        zIndex: 2,
                      }}>
                        {step.status === 'completed' ? '✓' : step.status === 'in_progress' ? '⟳' : index + 1}
                      </div>

                      <div style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '1rem',
                      }}>
                        <div style={{
                          fontSize: '1.5rem',
                          lineHeight: '1',
                        }}>
                          {getStatusIcon(step.status)}
                        </div>
                        <div style={{ flex: 1 }}>
                          <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'flex-start',
                            marginBottom: '0.5rem',
                          }}>
                            <p style={{
                              margin: 0,
                              fontWeight: '600',
                              color: '#1f2937',
                              fontSize: '1.125rem',
                            }}>
                              {step.step}
                            </p>
                            {step.timestamp && (
                              <span style={{
                                padding: '0.25rem 0.75rem',
                                borderRadius: '12px',
                                fontSize: '0.75rem',
                                fontWeight: '500',
                                background: getStatusColor(step.status) + '20',
                                color: getStatusColor(step.status),
                              }}>
                                {step.timestamp}
                              </span>
                            )}
                          </div>

                          {/* Status badge */}
                          <div style={{
                            display: 'flex',
                            gap: '0.5rem',
                            marginBottom: '0.75rem',
                            flexWrap: 'wrap',
                          }}>
                            <span style={{
                              padding: '0.25rem 0.75rem',
                              borderRadius: '12px',
                              fontSize: '0.75rem',
                              fontWeight: '500',
                              background: getStatusColor(step.status) + '20',
                              color: getStatusColor(step.status),
                              textTransform: 'capitalize',
                            }}>
                              {step.status.replace('_', ' ')}
                            </span>
                            {step.status === 'in_progress' && (
                              <span style={{
                                padding: '0.25rem 0.75rem',
                                borderRadius: '12px',
                                fontSize: '0.75rem',
                                fontWeight: '500',
                                background: '#fef3c7',
                                color: '#92400e',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.25rem',
                              }}>
                                <span style={{
                                  display: 'inline-block',
                                  width: '6px',
                                  height: '6px',
                                  borderRadius: '50%',
                                  background: '#f59e0b',
                                  animation: 'pulse 2s infinite',
                                }} />
                                Active
                              </span>
                            )}
                          </div>

                          {/* Expandable details */}
                          {isExpanded && stepDetails && (
                            <div style={{
                              marginTop: '1rem',
                              padding: '1rem',
                              background: 'white',
                              borderRadius: '8px',
                              border: '1px solid #e5e7eb',
                              animation: 'slideDown 0.3s ease',
                            }}>
                              <p style={{
                                margin: '0 0 0.75rem 0',
                                fontSize: '0.875rem',
                                fontWeight: '600',
                                color: '#374151',
                              }}>
                                Details:
                              </p>
                              <p style={{
                                margin: 0,
                                fontSize: '0.875rem',
                                color: '#6b7280',
                                lineHeight: '1.6',
                              }}>
                                {stepDetails.description}
                              </p>
                              {stepDetails.actions && stepDetails.actions.length > 0 && (
                                <div style={{
                                  marginTop: '0.75rem',
                                  paddingTop: '0.75rem',
                                  borderTop: '1px solid #e5e7eb',
                                }}>
                                  <p style={{
                                    margin: '0 0 0.5rem 0',
                                    fontSize: '0.875rem',
                                    fontWeight: '600',
                                    color: '#374151',
                                  }}>
                                    Actions taken:
                                  </p>
                                  <ul style={{
                                    margin: 0,
                                    paddingLeft: '1.25rem',
                                    fontSize: '0.875rem',
                                    color: '#6b7280',
                                  }}>
                                    {stepDetails.actions.map((action, idx) => (
                                      <li key={idx} style={{ marginBottom: '0.25rem' }}>
                                        {action}
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          )}

                          {/* Hover hint */}
                          {isHovered && !isExpanded && (
                            <p style={{
                              margin: '0.5rem 0 0 0',
                              fontSize: '0.75rem',
                              color: '#6b7280',
                              fontStyle: 'italic',
                            }}>
                              Click to see details
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Reasoning Log */}
          <div style={{
            background: 'white',
            borderRadius: '16px',
            padding: '2rem',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
            maxHeight: '500px',
            overflow: 'auto',
          }}>
            <h2 style={{
              fontSize: '1.5rem',
              fontWeight: '600',
              marginBottom: '1.5rem',
              color: '#1f2937',
            }}>
              💬 Reasoning Log / Memory
            </h2>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
            }}>
              {candidate.reasoningLog?.map((log, index) => (
                <div
                  key={index}
                  style={{
                    padding: '1rem',
                    background: '#f9fafb',
                    borderRadius: '8px',
                    borderLeft: `4px solid ${getLogTypeColor(log.type)}`,
                  }}
                >
                  <p style={{
                    margin: '0 0 0.5rem 0',
                    fontSize: '0.875rem',
                    color: '#6b7280',
                    fontWeight: '500',
                  }}>
                    {log.timestamp}
                  </p>
                  <p style={{
                    margin: 0,
                    color: '#1f2937',
                    lineHeight: '1.6',
                  }}>
                    {log.message}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>
    </main>
  )
}

