'use client'

import { useState, useEffect, FormEvent, ChangeEvent } from 'react'
import { CVUploadClient, DatabaseClient } from '@/lib/sdk'

interface FormData {
  fullName: string
  email: string
  phone: string
  cvFile: File | null
}

export default function CandidatePortal() {
  const [cvClient] = useState(() => new CVUploadClient())
  const [dbClient] = useState(() => new DatabaseClient())
  const [connected, setConnected] = useState(false)
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState<FormData>({
    fullName: '',
    email: '',
    phone: '',
    cvFile: null,
  })
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info' | 'warning'; text: string } | null>(null)
  const [showJobDescription, setShowJobDescription] = useState(false)
  const [applicationStatus, setApplicationStatus] = useState<string | null>(null)

  // Check API health on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const isHealthy = await cvClient.health()
        setConnected(isHealthy)
      } catch (error) {
        console.error('Failed to check API health:', error)
        setConnected(false)
      }
    }
    checkHealth()
  }, [cvClient])

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null
    setFormData(prev => ({ ...prev, cvFile: file }))
  }

  const checkStatus = async () => {
    if (!formData.email) return
    
    try {
      setApplicationStatus('Checking status...')
      const response = await dbClient.getCandidateByEmail(formData.email, true)
      
      if (response.success && response.data) {
        const candidate = response.data
        const status = candidate.status || 'unknown'
        const appliedDate = candidate.created_at 
          ? new Date(candidate.created_at).toLocaleDateString() 
          : 'N/A'
        
        let statusText = `Application Status: ${status}\n`
        statusText += `Applied: ${appliedDate}\n`
        
        if (candidate.cv_screening_results && candidate.cv_screening_results.length > 0) {
          const latestScreening = candidate.cv_screening_results[0]
          statusText += `CV Screening Score: ${(latestScreening.overall_fit_score * 100).toFixed(1)}%\n`
        }
        
        if (candidate.voice_screening_results && candidate.voice_screening_results.length > 0) {
          statusText += `Voice Screening: Completed\n`
        }
        
        if (candidate.interview_scheduling && candidate.interview_scheduling.length > 0) {
          const interview = candidate.interview_scheduling[0]
          statusText += `Interview: ${interview.status || 'Scheduled'}\n`
        }
        
        if (candidate.final_decision) {
          statusText += `Final Decision: ${candidate.final_decision.decision || 'Pending'}\n`
        }
        
        setApplicationStatus(statusText)
      } else {
        setApplicationStatus(`No application found for ${formData.email}. Please submit an application first.`)
      }
    } catch (error: any) {
      setApplicationStatus(`Error: ${error.message || 'Failed to check status'}`)
    }
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setMessage(null)

    // Validation
    if (!formData.fullName || !formData.email) {
      setMessage({ type: 'error', text: 'Full name and email are required.' })
      return
    }

    if (!formData.cvFile) {
      setMessage({ type: 'error', text: 'Please upload your CV before submitting.' })
      return
    }

    // Check file type
    const fileExt = formData.cvFile.name.split('.').pop()?.toLowerCase()
    if (fileExt !== 'pdf' && fileExt !== 'docx') {
      setMessage({ type: 'error', text: 'Please upload a PDF or DOCX file.' })
      return
    }

    if (!connected) {
      setMessage({ type: 'error', text: 'Backend not connected. Please try again later.' })
      return
    }

    setLoading(true)
    setMessage({ type: 'info', text: '💾 Registering your application...' })

    try {
      const response = await cvClient.submit(
        formData.fullName,
        formData.email,
        formData.cvFile,
        formData.cvFile.name,
        formData.phone || ''
      )

      if (response.success) {
        setMessage({ 
          type: 'success', 
          text: `✅ ${response.message || `Application submitted successfully for ${formData.fullName}! Your application has been recorded. You will receive updates soon.`}` 
        })
        // Reset form
        setFormData({
          fullName: '',
          email: '',
          phone: '',
          cvFile: null,
        })
        // Reset file input
        const fileInput = document.getElementById('cvFile') as HTMLInputElement
        if (fileInput) fileInput.value = ''
      } else if (response.already_exists) {
        setMessage({ 
          type: 'warning', 
          text: `⚠️ ${response.message || `An application with ${formData.email} already exists. You can only apply once — please wait for review.`}` 
        })
      } else {
        setMessage({ type: 'error', text: response.message || 'Failed to submit application' })
      }
    } catch (error: any) {
      setMessage({ type: 'error', text: `Failed to submit application: ${error.message || 'Unknown error'}` })
      console.error('Submission error:', error)
    } finally {
      setLoading(false)
    }
  }

  const getMessageStyle = () => {
    if (!message) return {}
    const baseStyle = {
      padding: '1rem',
      borderRadius: '8px',
      marginBottom: '1.5rem',
      fontWeight: '500' as const,
    }
    switch (message.type) {
      case 'success':
        return { ...baseStyle, background: '#d1fae5', color: '#065f46', border: '1px solid #10b981' }
      case 'error':
        return { ...baseStyle, background: '#fee2e2', color: '#991b1b', border: '1px solid #ef4444' }
      case 'warning':
        return { ...baseStyle, background: '#fef3c7', color: '#92400e', border: '1px solid #f59e0b' }
      case 'info':
        return { ...baseStyle, background: '#dbeafe', color: '#1e40af', border: '1px solid #3b82f6' }
      default:
        return baseStyle
    }
  }

  return (
    <main style={{ 
      minHeight: '100vh', 
      padding: '2rem 1rem',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'flex-start',
    }}>
      <div style={{
        background: 'white',
        borderRadius: '16px',
        padding: '2.5rem',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        maxWidth: '600px',
        width: '100%',
      }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={{ 
            fontSize: '2.5rem',
            fontWeight: 'bold',
            color: '#1f2937',
            marginBottom: '0.5rem',
          }}>
            🤖 AI Engineer Job Application Portal
          </h1>
          <p style={{ 
            fontSize: '1.125rem',
            color: '#6b7280',
            lineHeight: '1.6',
          }}>
            Welcome to <strong>ScionHire AI Labs</strong> 👋<br />
            We're seeking talented engineers passionate about building intelligent systems!<br />
            Please submit your CV below to apply for the <strong>AI Engineer</strong> position.
          </p>
        </div>

        {/* Connection Status */}
        {!connected && (
          <div style={{
            padding: '1rem',
            background: '#fee2e2',
            borderRadius: '8px',
            marginBottom: '1.5rem',
            color: '#991b1b',
            fontSize: '0.875rem',
          }}>
            ⚠️ Backend not connected. Some features may not work.
          </div>
        )}

        {/* Job Description */}
        <div style={{ marginBottom: '2rem' }}>
          <button
            onClick={() => setShowJobDescription(!showJobDescription)}
            style={{
              width: '100%',
              padding: '1rem',
              background: '#f3f4f6',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '1rem',
              fontWeight: '500',
              color: '#374151',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span>📄 View Job Description</span>
            <span>{showJobDescription ? '▲' : '▼'}</span>
          </button>
          
          {showJobDescription && (
            <div style={{
              marginTop: '1rem',
              padding: '1.5rem',
              background: '#f9fafb',
              borderRadius: '8px',
              border: '1px solid #e5e7eb',
            }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem', color: '#1f2937' }}>
                🧠 Position: AI Engineer
              </h3>
              <p style={{ marginBottom: '0.75rem', color: '#4b5563' }}>
                <strong>Location:</strong> Remote / Wiesbaden HQ
              </p>
              <div style={{ marginBottom: '1rem' }}>
                <p style={{ fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>About the Role:</p>
                <p style={{ color: '#6b7280', lineHeight: '1.6' }}>
                  Join our AI R&D team to develop, fine-tune, and deploy ML models for production.
                  You will work on projects involving LLMs, LangGraph agents, and context engineering.
                </p>
              </div>
              <div>
                <p style={{ fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>Requirements:</p>
                <ul style={{ color: '#6b7280', lineHeight: '1.8', paddingLeft: '1.5rem' }}>
                  <li>Proficiency in Python & modern AI frameworks (PyTorch, LangChain, etc.)</li>
                  <li>Solid understanding of NLP and ML pipelines</li>
                  <li>Experience deploying models or building intelligent systems</li>
                  <li>Strong communication and teamwork skills</li>
                </ul>
              </div>
            </div>
          )}
        </div>

        <div style={{ height: '1px', background: '#e5e7eb', marginBottom: '2rem' }} />

        {/* Application Form */}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1.5rem' }}>
            <label 
              htmlFor="fullName"
              style={{ 
                display: 'block', 
                marginBottom: '0.5rem',
                fontWeight: '500',
                color: '#374151',
              }}
            >
              Full Name *
            </label>
            <input
              type="text"
              id="fullName"
              name="fullName"
              value={formData.fullName}
              onChange={handleInputChange}
              placeholder="Ada Lovelace"
              required
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #d1d5db',
                borderRadius: '8px',
                fontSize: '1rem',
                fontFamily: 'inherit',
              }}
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label 
              htmlFor="email"
              style={{ 
                display: 'block', 
                marginBottom: '0.5rem',
                fontWeight: '500',
                color: '#374151',
              }}
            >
              Email Address *
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              placeholder="ada@lovelabs.ai"
              required
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #d1d5db',
                borderRadius: '8px',
                fontSize: '1rem',
                fontFamily: 'inherit',
              }}
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label 
              htmlFor="phone"
              style={{ 
                display: 'block', 
                marginBottom: '0.5rem',
                fontWeight: '500',
                color: '#374151',
              }}
            >
              Phone Number
            </label>
            <input
              type="tel"
              id="phone"
              name="phone"
              value={formData.phone}
              onChange={handleInputChange}
              placeholder="+49 170 1234567"
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #d1d5db',
                borderRadius: '8px',
                fontSize: '1rem',
                fontFamily: 'inherit',
              }}
            />
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <label 
              htmlFor="cvFile"
              style={{ 
                display: 'block', 
                marginBottom: '0.5rem',
                fontWeight: '500',
                color: '#374151',
              }}
            >
              Upload Your CV (PDF or DOCX) *
            </label>
            <input
              type="file"
              id="cvFile"
              name="cvFile"
              accept=".pdf,.docx"
              onChange={handleFileChange}
              required
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #d1d5db',
                borderRadius: '8px',
                fontSize: '1rem',
                fontFamily: 'inherit',
                background: '#f9fafb',
              }}
            />
            {formData.cvFile && (
              <p style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: '#6b7280' }}>
                Selected: {formData.cvFile.name}
              </p>
            )}
          </div>

          {message && (
            <div style={getMessageStyle()}>
              {message.text}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !connected}
            style={{
              width: '100%',
              padding: '1rem',
              background: loading || !connected ? '#9ca3af' : '#2563eb',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '1.125rem',
              fontWeight: '600',
              cursor: loading || !connected ? 'not-allowed' : 'pointer',
              transition: 'background 0.2s',
              marginBottom: '1rem',
            }}
          >
            {loading ? '⏳ Processing...' : '📨 Submit Application'}
          </button>
        </form>

        {/* Check Status Section */}
        <div style={{
          marginTop: '2rem',
          padding: '1.5rem',
          background: '#f9fafb',
          borderRadius: '8px',
          border: '1px solid #e5e7eb',
        }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem', color: '#1f2937' }}>
            📊 Check Application Status
          </h3>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
            <input
              type="email"
              placeholder="Enter your email"
              value={formData.email}
              onChange={handleInputChange}
              name="email"
              style={{
                flex: 1,
                padding: '0.75rem',
                border: '1px solid #d1d5db',
                borderRadius: '8px',
                fontSize: '1rem',
              }}
            />
            <button
              onClick={checkStatus}
              disabled={!connected || !formData.email}
              style={{
                padding: '0.75rem 1.5rem',
                background: connected && formData.email ? '#2563eb' : '#9ca3af',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '1rem',
                fontWeight: '500',
                cursor: connected && formData.email ? 'pointer' : 'not-allowed',
              }}
            >
              Check
            </button>
          </div>
          {applicationStatus && (
            <div style={{
              padding: '1rem',
              background: 'white',
              borderRadius: '8px',
              border: '1px solid #e5e7eb',
              fontSize: '0.875rem',
              color: '#374151',
            }}>
              {applicationStatus}
            </div>
          )}
        </div>
      </div>
    </main>
  )
}

