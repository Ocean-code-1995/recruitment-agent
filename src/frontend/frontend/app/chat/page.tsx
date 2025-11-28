'use client'

import { useState, useEffect, useRef, FormEvent } from 'react'
import { SupervisorClient } from '@/lib/sdk'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  tokenCount?: number
}

export default function SupervisorChat() {
  const [supervisorClient] = useState(() => new SupervisorClient())
  const [connected, setConnected] = useState(false)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [chatInput, setChatInput] = useState('')
  const [sendingMessage, setSendingMessage] = useState(false)
  const [threadId, setThreadId] = useState<string | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [totalTokens, setTotalTokens] = useState(0)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Check API health and initialize chat
  useEffect(() => {
    const initChat = async () => {
      try {
        const isHealthy = await supervisorClient.health()
        setConnected(isHealthy)
        
        if (isHealthy) {
          // Create new chat session
          const newThreadId = await supervisorClient.newChat()
          setThreadId(newThreadId)
          
          // Initialize with welcome message
          setChatMessages([
            {
              id: '1',
              role: 'assistant',
              content: "Hello! I'm the HR Supervisor Agent. I can help you with:\n\n• Querying candidate information\n• Screening CVs\n• Scheduling interviews\n• Managing the recruitment pipeline\n• Answering questions about candidates\n\nWhat would you like to know?",
              timestamp: new Date().toISOString(),
            },
          ])
        }
      } catch (error) {
        console.error('Failed to initialize chat:', error)
        setConnected(false)
      }
    }
    initChat()
  }, [supervisorClient])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages])

  const handleSendMessage = async (e: FormEvent) => {
    e.preventDefault()
    if (!chatInput.trim() || sendingMessage || !connected) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: chatInput,
      timestamp: new Date().toISOString(),
    }

    setChatMessages(prev => [...prev, userMessage])
    const currentInput = chatInput
    setChatInput('')
    setSendingMessage(true)
    setIsStreaming(false)

    try {
      // Use batch chat (more reliable than streaming)
      const response = await supervisorClient.chat(
        currentInput,
        threadId || undefined
      )

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.content,
        timestamp: new Date().toISOString(),
        tokenCount: response.token_count,
      }

      setChatMessages(prev => [...prev, assistantMessage])
      
      // Update total token count
      if (response.token_count) {
        setTotalTokens(prev => prev + response.token_count)
      }
      
      // Update thread ID if we got a new one
      if (response.thread_id && response.thread_id !== threadId) {
        setThreadId(response.thread_id)
      }
    } catch (error: any) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `❌ Error: ${error.message || 'Failed to get response from supervisor agent. Please try again.'}`,
        timestamp: new Date().toISOString(),
      }
      setChatMessages(prev => [...prev, errorMessage])
      console.error('Failed to send message:', error)
    } finally {
      setSendingMessage(false)
      setIsStreaming(false)
    }
  }

  const handleNewChat = async () => {
    try {
      const newThreadId = await supervisorClient.newChat()
      setThreadId(newThreadId)
      setTotalTokens(0) // Reset token count for new chat
      setChatMessages([
        {
          id: '1',
          role: 'assistant',
          content: "New chat session started! How can I help you today?",
          timestamp: new Date().toISOString(),
        },
      ])
    } catch (error: any) {
      alert(`Failed to create new chat: ${error.message || 'Unknown error'}`)
    }
  }

  return (
    <main style={{
      minHeight: '100vh',
      padding: '2rem',
      background: '#f9fafb',
    }}>
      <div style={{
        maxWidth: '1200px',
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
                🤖 Supervisor Agent Chat
              </h1>
              <p style={{
                fontSize: '1.125rem',
                color: '#6b7280',
              }}>
                Interact with the HR Supervisor Agent to manage recruitment
              </p>
            </div>
            <div style={{
              display: 'flex',
              gap: '0.5rem',
            }}>
              <button
                onClick={handleNewChat}
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
                🆕 New Chat
              </button>
              {threadId && (
                <div style={{
                  padding: '0.75rem 1rem',
                  background: '#f3f4f6',
                  borderRadius: '8px',
                  fontSize: '0.875rem',
                  color: '#6b7280',
                }}>
                  Thread: {threadId}
                </div>
              )}
              {totalTokens > 0 && (
                <div style={{
                  padding: '0.75rem 1rem',
                  background: '#dbeafe',
                  borderRadius: '8px',
                  fontSize: '0.875rem',
                  color: '#1e40af',
                  fontWeight: '500',
                }}>
                  📊 Total: {totalTokens.toLocaleString()} tokens
                </div>
              )}
            </div>
          </div>
        </div>

        {!connected && (
          <div style={{
            padding: '1rem',
            background: '#fee2e2',
            borderRadius: '8px',
            marginBottom: '2rem',
            color: '#991b1b',
          }}>
            ⚠️ Supervisor API not connected. Please make sure the backend is running.
          </div>
        )}

        {/* Chat Interface */}
        <div style={{
          background: 'white',
          borderRadius: '16px',
          padding: '2rem',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          display: 'flex',
          flexDirection: 'column',
          height: 'calc(100vh - 300px)',
          minHeight: '600px',
        }}>
          {/* Chat Messages */}
          <div style={{
            flex: 1,
            overflowY: 'auto',
            marginBottom: '1.5rem',
            padding: '1rem',
            background: '#f9fafb',
            borderRadius: '8px',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
          }}>
            {chatMessages.map((message) => (
              <div
                key={message.id}
                style={{
                  display: 'flex',
                  justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
                }}
              >
                <div style={{
                  maxWidth: '75%',
                  padding: '1rem 1.25rem',
                  borderRadius: '12px',
                  background: message.role === 'user' ? '#2563eb' : '#e5e7eb',
                  color: message.role === 'user' ? 'white' : '#1f2937',
                  boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
                }}>
                  <p style={{
                    margin: 0,
                    lineHeight: '1.6',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}>
                    {message.content}
                  </p>
                  <div style={{
                    marginTop: '0.5rem',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    fontSize: '0.75rem',
                    opacity: 0.7,
                  }}>
                    <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
                    {message.tokenCount && (
                      <span style={{
                        marginLeft: '0.5rem',
                        padding: '0.125rem 0.5rem',
                        background: message.role === 'user' 
                          ? 'rgba(255, 255, 255, 0.2)' 
                          : '#dbeafe',
                        borderRadius: '4px',
                        color: message.role === 'user' ? 'white' : '#1e40af',
                        fontWeight: '500',
                        fontSize: '0.7rem',
                      }}>
                        {message.tokenCount.toLocaleString()} tokens
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {sendingMessage && (
              <div style={{
                display: 'flex',
                justifyContent: 'flex-start',
              }}>
                <div style={{
                  padding: '1rem 1.25rem',
                  borderRadius: '12px',
                  background: '#e5e7eb',
                  color: '#6b7280',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                }}>
                  <span style={{
                    display: 'inline-block',
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    background: '#6b7280',
                    animation: 'pulse 1.5s infinite',
                  }} />
                  Agent is thinking...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input */}
          <form onSubmit={handleSendMessage} style={{
            display: 'flex',
            gap: '0.5rem',
          }}>
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Ask about candidates, schedule interviews, or query the database..."
              disabled={sendingMessage || !connected}
              style={{
                flex: 1,
                padding: '0.75rem 1rem',
                border: '1px solid #d1d5db',
                borderRadius: '8px',
                fontSize: '1rem',
                fontFamily: 'inherit',
                background: sendingMessage || !connected ? '#f3f4f6' : 'white',
              }}
            />
            <button
              type="submit"
              disabled={sendingMessage || !chatInput.trim() || !connected}
              style={{
                padding: '0.75rem 1.5rem',
                background: sendingMessage || !chatInput.trim() || !connected ? '#9ca3af' : '#2563eb',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '1rem',
                fontWeight: '500',
                cursor: sendingMessage || !chatInput.trim() || !connected ? 'not-allowed' : 'pointer',
                transition: 'background 0.2s',
              }}
            >
              {sendingMessage ? '⏳' : '📤'} Send
            </button>
          </form>

          {/* Helper text */}
          <div style={{
            marginTop: '0.75rem',
            padding: '0.75rem',
            background: '#f3f4f6',
            borderRadius: '6px',
            fontSize: '0.875rem',
            color: '#6b7280',
          }}>
            💡 <strong>Tip:</strong> Try asking "Show me all candidates", "What's the status of [email]?", or "Schedule an interview for [candidate name]"
          </div>
        </div>
      </div>
    </main>
  )
}

