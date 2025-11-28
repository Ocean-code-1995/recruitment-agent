/**
 * Supervisor API Client
 * 
 * A TypeScript client for interacting with the HR Supervisor Agent API.
 * Supports both regular and streaming responses.
 * 
 * This mirrors the Python SDK's SupervisorClient functionality.
 */

import { getBaseUrl } from './config';
import { ChatResponse, StreamChunk, NewChatResponse } from './types';

export class SupervisorClient {
  private baseUrl: string;

  /**
   * Initialize the Supervisor client.
   * 
   * @param baseUrl Optional API base URL. Defaults to SUPERVISOR_API_URL env var
   *                or http://localhost:8080/api/v1/supervisor
   */
  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || getBaseUrl('supervisor');
  }

  /**
   * Send a message and get a complete response.
   * 
   * Uses CompactingSupervisor wrapper for automatic context management.
   * When token limit is exceeded, old messages are compacted/summarized.
   * 
   * @param message The message to send
   * @param threadId Optional thread ID for conversation continuity
   * @param timeout Request timeout in milliseconds (default: 120000)
   * @returns ChatResponse with content, thread_id, and token_count
   */
  async chat(
    message: string,
    threadId?: string,
    timeout: number = 120000
  ): Promise<ChatResponse> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(`${this.baseUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          thread_id: threadId,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(`API error: ${error.detail || 'Unknown error'}`);
      }

      const data = await response.json();
      return {
        content: data.response,
        thread_id: data.thread_id,
        token_count: data.token_count,
      };
    } catch (error: any) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new Error('Request timed out');
      }
      throw error;
    }
  }

  /**
   * Send a message and stream the response token by token.
   * 
   * ⚠️ WARNING: This method may have known issues.
   * Use chat() for reliable batch requests.
   * 
   * Uses CompactingSupervisor wrapper for automatic context management.
   * 
   * @param message The message to send
   * @param threadId Optional thread ID for conversation continuity
   * @param timeout Request timeout in milliseconds (default: 300000)
   * @param onChunk Callback function for each chunk received
   */
  async stream(
    message: string,
    threadId: string | undefined,
    onChunk: (chunk: StreamChunk) => void,
    timeout: number = 300000
  ): Promise<void> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(`${this.baseUrl}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          thread_id: threadId,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        onChunk({
          type: 'error',
          error: `API returned status ${response.status}`,
        });
        return;
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let currentEvent: string | null = null;

      if (!reader) {
        onChunk({
          type: 'error',
          error: 'No response body',
        });
        return;
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('event:')) {
            currentEvent = line.substring(6).trim();
          } else if (line.startsWith('data:') && currentEvent) {
            try {
              const jsonStr = line.substring(5).trim();
              const data = JSON.parse(jsonStr);

              if (currentEvent === 'token') {
                onChunk({
                  type: 'token',
                  content: data.content || '',
                });
              } else if (currentEvent === 'done') {
                onChunk({
                  type: 'done',
                  thread_id: data.thread_id,
                  token_count: data.token_count || 0,
                });
              } else if (currentEvent === 'error') {
                onChunk({
                  type: 'error',
                  error: data.error || 'Unknown error',
                });
              }
            } catch (e) {
              // Skip invalid JSON
            }
            currentEvent = null;
          }
        }
      }
    } catch (error: any) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        onChunk({
          type: 'error',
          error: 'Request timed out',
        });
      } else if (error.message?.includes('fetch')) {
        onChunk({
          type: 'error',
          error: 'Cannot connect to API. Make sure the server is running.',
        });
      } else {
        onChunk({
          type: 'error',
          error: error.message || String(error),
        });
      }
    }
  }

  /**
   * Create a new chat session.
   * 
   * @returns New thread_id
   */
  async newChat(): Promise<string> {
    const response = await fetch(`${this.baseUrl}/new`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error(`Failed to create new chat: ${response.statusText}`);
    }

    const data: NewChatResponse = await response.json();
    return data.thread_id;
  }

  /**
   * Send a message to the raw supervisor agent (without context compaction).
   * 
   * This bypasses the CompactingSupervisor wrapper, giving direct access
   * to the underlying supervisor agent.
   * 
   * @param message The message to send
   * @param threadId Optional thread ID for conversation continuity
   * @param timeout Request timeout in milliseconds (default: 120000)
   * @returns ChatResponse with content, thread_id, and token_count
   */
  async chatRaw(
    message: string,
    threadId?: string,
    timeout: number = 120000
  ): Promise<ChatResponse> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(`${this.baseUrl}/raw/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          thread_id: threadId,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(`API error: ${error.detail || 'Unknown error'}`);
      }

      const data = await response.json();
      return {
        content: data.response,
        thread_id: data.thread_id,
        token_count: data.token_count,
      };
    } catch (error: any) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new Error('Request timed out');
      }
      throw error;
    }
  }

  /**
   * Stream a response from the raw supervisor agent (without context compaction).
   * 
   * ⚠️ WARNING: This method may have known issues.
   * Use chatRaw() for reliable batch requests.
   * 
   * @param message The message to send
   * @param threadId Optional thread ID for conversation continuity
   * @param onChunk Callback function for each chunk received
   * @param timeout Request timeout in milliseconds (default: 300000)
   */
  async streamRaw(
    message: string,
    threadId: string | undefined,
    onChunk: (chunk: StreamChunk) => void,
    timeout: number = 300000
  ): Promise<void> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(`${this.baseUrl}/raw/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          thread_id: threadId,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        onChunk({
          type: 'error',
          error: `API returned status ${response.status}`,
        });
        return;
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let currentEvent: string | null = null;

      if (!reader) {
        onChunk({
          type: 'error',
          error: 'No response body',
        });
        return;
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('event:')) {
            currentEvent = line.substring(6).trim();
          } else if (line.startsWith('data:') && currentEvent) {
            try {
              const jsonStr = line.substring(5).trim();
              const data = JSON.parse(jsonStr);

              if (currentEvent === 'token') {
                onChunk({
                  type: 'token',
                  content: data.content || '',
                });
              } else if (currentEvent === 'done') {
                onChunk({
                  type: 'done',
                  thread_id: data.thread_id,
                  token_count: data.token_count || 0,
                });
              } else if (currentEvent === 'error') {
                onChunk({
                  type: 'error',
                  error: data.error || 'Unknown error',
                });
              }
            } catch (e) {
              // Skip invalid JSON
            }
            currentEvent = null;
          }
        }
      }
    } catch (error: any) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        onChunk({
          type: 'error',
          error: 'Request timed out',
        });
      } else if (error.message?.includes('fetch')) {
        onChunk({
          type: 'error',
          error: 'Cannot connect to API. Make sure the server is running.',
        });
      } else {
        onChunk({
          type: 'error',
          error: error.message || String(error),
        });
      }
    }
  }

  /**
   * Check if the API is healthy.
   * 
   * @returns True if healthy, False otherwise
   */
  async health(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000),
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}

