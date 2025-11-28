/**
 * Voice Screening API Client
 * 
 * A TypeScript client for managing voice screening sessions.
 */

import { getBaseUrl } from './config';

export interface CreateSessionRequest {
  candidate_id: string;
}

export interface CreateSessionResponse {
  session_id: string;
  candidate_name: string;
  job_title: string;
  message: string;
}

export interface SessionConfigResponse {
  candidate_name: string;
  job_title: string;
  instructions: string;
  questions: string[];
  config: Record<string, any>;
}

export class VoiceScreeningClient {
  private baseUrl: string;

  /**
   * Initialize the Voice Screening client.
   * 
   * @param baseUrl Optional API base URL. Defaults to VOICE_SCREENER_API_URL env var
   *                or http://localhost:8080/api/v1/voice-screener
   */
  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || getBaseUrl('voice-screener');
  }

  /**
   * Create a new voice screening session for a candidate.
   * 
   * @param candidateId Candidate UUID
   * @returns CreateSessionResponse with session_id and candidate info
   */
  async createSession(candidateId: string): Promise<CreateSessionResponse> {
    const response = await fetch(`${this.baseUrl}/session/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        candidate_id: candidateId,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(`Failed to create session: ${error.detail || 'Unknown error'}`);
    }

    return await response.json();
  }

  /**
   * Get session configuration.
   * 
   * @param sessionId Session ID
   * @param candidateId Candidate UUID
   * @returns SessionConfigResponse with interview configuration
   */
  async getSessionConfig(sessionId: string, candidateId: string): Promise<SessionConfigResponse> {
    const params = new URLSearchParams({ candidate_id: candidateId });
    const response = await fetch(`${this.baseUrl}/session/${sessionId}/config?${params}`, {
      method: 'GET',
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(`Failed to get session config: ${error.detail || 'Unknown error'}`);
    }

    return await response.json();
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

