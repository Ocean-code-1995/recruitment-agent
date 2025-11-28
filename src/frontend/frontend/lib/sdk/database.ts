/**
 * Database API Client
 * 
 * A TypeScript client for querying the recruitment database via the API.
 * This mirrors the Python SDK's DatabaseClient functionality.
 */

import { getBaseUrl } from './config';
import { QueryResponse, SingleRecordResponse, StatsResponse } from './types';

export class DatabaseClient {
  private baseUrl: string;
  private timeout: number;

  /**
   * Initialize the Database client.
   * 
   * @param baseUrl Optional API base URL. Defaults to DATABASE_API_URL env var
   *                or http://localhost:8080/api/v1/db
   */
  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || getBaseUrl('database');
    this.timeout = 30000;
  }

  /**
   * Flexible query for any table.
   * 
   * @param table Table name (candidates, cv_screening_results, voice_screening_results, 
   *              interview_scheduling, final_decision)
   * @param filters Key-value filters. Supports operators like {"field": {"$gte": 0.8}}
   * @param fields Specific fields to return. None returns all.
   * @param includeRelations Include related data (candidates table only)
   * @param limit Max records to return
   * @param offset Number of records to skip
   * @param sortBy Field to sort by
   * @param sortOrder "asc" or "desc"
   * @returns QueryResponse with data and pagination info
   */
  async query(
    table: string,
    filters?: Record<string, any>,
    fields?: string[],
    includeRelations: boolean = false,
    limit: number = 100,
    offset: number = 0,
    sortBy?: string,
    sortOrder: 'asc' | 'desc' = 'desc'
  ): Promise<QueryResponse> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${this.baseUrl}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          table,
          filters: filters || null,
          fields: fields || null,
          include_relations: includeRelations,
          limit,
          offset,
          sort_by: sortBy || null,
          sort_order: sortOrder,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        if (response.status === 400) {
          throw new Error(`Validation error: ${error.detail || 'Invalid request'}`);
        } else if (response.status === 500) {
          throw new Error(`Server error: ${error.detail || 'Server error'}`);
        } else {
          throw new Error(`Unexpected status: ${response.status}`);
        }
      }

      const data = await response.json();
      return {
        success: data.success,
        table: data.table,
        total_count: data.total_count,
        returned_count: data.returned_count,
        offset: data.offset,
        data: data.data,
        message: data.message,
      };
    } catch (error: any) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  /**
   * List all candidates with optional filtering.
   * 
   * @param status Filter by status (e.g., "applied", "screening", "interviewed")
   * @param limit Max records to return
   * @param offset Pagination offset
   * @param includeRelations Include CV/voice screening results, interviews, decisions
   * @returns QueryResponse with candidate data
   */
  async getCandidates(
    status?: string,
    limit: number = 100,
    offset: number = 0,
    includeRelations: boolean = false
  ): Promise<QueryResponse> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
      include_relations: includeRelations.toString(),
    });
    if (status) {
      params.append('status', status);
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${this.baseUrl}/candidates?${params}`, {
        method: 'GET',
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        if (response.status === 400) {
          throw new Error(`Validation error: ${error.detail || 'Invalid request'}`);
        } else if (response.status === 500) {
          throw new Error(`Server error: ${error.detail || 'Server error'}`);
        } else {
          throw new Error(`Unexpected status: ${response.status}`);
        }
      }

      const data = await response.json();
      return {
        success: data.success,
        table: data.table,
        total_count: data.total_count,
        returned_count: data.returned_count,
        offset: data.offset,
        data: data.data,
        message: data.message,
      };
    } catch (error: any) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  /**
   * Get a single candidate by ID with all related data.
   * 
   * @param candidateId Candidate UUID
   * @param includeRelations Include CV/voice screening, interviews, decisions
   * @returns SingleRecordResponse with full candidate profile
   */
  async getCandidate(
    candidateId: string,
    includeRelations: boolean = true
  ): Promise<SingleRecordResponse> {
    const params = new URLSearchParams({
      include_relations: includeRelations.toString(),
    });

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${this.baseUrl}/candidates/${candidateId}?${params}`, {
        method: 'GET',
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        if (response.status === 400) {
          throw new Error(`Validation error: ${error.detail || 'Invalid request'}`);
        } else if (response.status === 500) {
          throw new Error(`Server error: ${error.detail || 'Server error'}`);
        } else {
          throw new Error(`Unexpected status: ${response.status}`);
        }
      }

      const data = await response.json();
      return {
        success: data.success,
        table: data.table,
        data: data.data,
        message: data.message,
      };
    } catch (error: any) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  /**
   * Get a candidate by email address with all related data.
   * 
   * @param email Candidate's email address
   * @param includeRelations Include CV/voice screening, interviews, decisions
   * @returns SingleRecordResponse with full candidate profile
   */
  async getCandidateByEmail(
    email: string,
    includeRelations: boolean = true
  ): Promise<SingleRecordResponse> {
    const params = new URLSearchParams({
      include_relations: includeRelations.toString(),
    });

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${this.baseUrl}/candidates/email/${encodeURIComponent(email)}?${params}`, {
        method: 'GET',
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        if (response.status === 400) {
          throw new Error(`Validation error: ${error.detail || 'Invalid request'}`);
        } else if (response.status === 500) {
          throw new Error(`Server error: ${error.detail || 'Server error'}`);
        } else {
          throw new Error(`Unexpected status: ${response.status}`);
        }
      }

      const data = await response.json();
      return {
        success: data.success,
        table: data.table,
        data: data.data,
        message: data.message,
      };
    } catch (error: any) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  /**
   * List CV screening results.
   * 
   * @param candidateId Filter by candidate
   * @param minScore Minimum overall fit score (0.0 - 1.0)
   * @param limit Max records
   * @param offset Pagination offset
   * @returns QueryResponse with CV screening results
   */
  async getCvScreenings(
    candidateId?: string,
    minScore?: number,
    limit: number = 100,
    offset: number = 0
  ): Promise<QueryResponse> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    if (candidateId) {
      params.append('candidate_id', candidateId);
    }
    if (minScore !== undefined) {
      params.append('min_score', minScore.toString());
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${this.baseUrl}/cv-screening?${params}`, {
        method: 'GET',
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        if (response.status === 400) {
          throw new Error(`Validation error: ${error.detail || 'Invalid request'}`);
        } else if (response.status === 500) {
          throw new Error(`Server error: ${error.detail || 'Server error'}`);
        } else {
          throw new Error(`Unexpected status: ${response.status}`);
        }
      }

      const data = await response.json();
      return {
        success: data.success,
        table: data.table,
        total_count: data.total_count,
        returned_count: data.returned_count,
        offset: data.offset,
        data: data.data,
        message: data.message,
      };
    } catch (error: any) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  /**
   * List voice screening results.
   * 
   * @param candidateId Filter by candidate
   * @param limit Max records
   * @param offset Pagination offset
   * @returns QueryResponse with voice screening results
   */
  async getVoiceScreenings(
    candidateId?: string,
    limit: number = 100,
    offset: number = 0
  ): Promise<QueryResponse> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    if (candidateId) {
      params.append('candidate_id', candidateId);
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${this.baseUrl}/voice-screening?${params}`, {
        method: 'GET',
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        if (response.status === 400) {
          throw new Error(`Validation error: ${error.detail || 'Invalid request'}`);
        } else if (response.status === 500) {
          throw new Error(`Server error: ${error.detail || 'Server error'}`);
        } else {
          throw new Error(`Unexpected status: ${response.status}`);
        }
      }

      const data = await response.json();
      return {
        success: data.success,
        table: data.table,
        total_count: data.total_count,
        returned_count: data.returned_count,
        offset: data.offset,
        data: data.data,
        message: data.message,
      };
    } catch (error: any) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  /**
   * List interview scheduling records.
   * 
   * @param candidateId Filter by candidate
   * @param status Filter by interview status
   * @param limit Max records
   * @param offset Pagination offset
   * @returns QueryResponse with interview data
   */
  async getInterviews(
    candidateId?: string,
    status?: string,
    limit: number = 100,
    offset: number = 0
  ): Promise<QueryResponse> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    if (candidateId) {
      params.append('candidate_id', candidateId);
    }
    if (status) {
      params.append('status', status);
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${this.baseUrl}/interviews?${params}`, {
        method: 'GET',
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        if (response.status === 400) {
          throw new Error(`Validation error: ${error.detail || 'Invalid request'}`);
        } else if (response.status === 500) {
          throw new Error(`Server error: ${error.detail || 'Server error'}`);
        } else {
          throw new Error(`Unexpected status: ${response.status}`);
        }
      }

      const data = await response.json();
      return {
        success: data.success,
        table: data.table,
        total_count: data.total_count,
        returned_count: data.returned_count,
        offset: data.offset,
        data: data.data,
        message: data.message,
      };
    } catch (error: any) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  /**
   * List final hiring decisions.
   * 
   * @param decision Filter by decision (e.g., "hired", "rejected")
   * @param minScore Minimum overall score
   * @param limit Max records
   * @param offset Pagination offset
   * @returns QueryResponse with decision data
   */
  async getDecisions(
    decision?: string,
    minScore?: number,
    limit: number = 100,
    offset: number = 0
  ): Promise<QueryResponse> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    if (decision) {
      params.append('decision', decision);
    }
    if (minScore !== undefined) {
      params.append('min_score', minScore.toString());
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${this.baseUrl}/decisions?${params}`, {
        method: 'GET',
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        if (response.status === 400) {
          throw new Error(`Validation error: ${error.detail || 'Invalid request'}`);
        } else if (response.status === 500) {
          throw new Error(`Server error: ${error.detail || 'Server error'}`);
        } else {
          throw new Error(`Unexpected status: ${response.status}`);
        }
      }

      const data = await response.json();
      return {
        success: data.success,
        table: data.table,
        total_count: data.total_count,
        returned_count: data.returned_count,
        offset: data.offset,
        data: data.data,
        message: data.message,
      };
    } catch (error: any) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  /**
   * Get database statistics.
   * 
   * @returns StatsResponse with counts for all tables and status breakdown
   */
  async getStats(): Promise<StatsResponse> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${this.baseUrl}/stats`, {
        method: 'GET',
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        if (response.status === 400) {
          throw new Error(`Validation error: ${error.detail || 'Invalid request'}`);
        } else if (response.status === 500) {
          throw new Error(`Server error: ${error.detail || 'Server error'}`);
        } else {
          throw new Error(`Unexpected status: ${response.status}`);
        }
      }

      const data = await response.json();
      return {
        success: data.success,
        stats: data.stats,
      };
    } catch (error: any) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  /**
   * Check if the database API is healthy.
   * 
   * @returns True if healthy, False otherwise
   */
  async health(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000),
      });
      const data = await response.json();
      return response.ok && data.status === 'healthy';
    } catch {
      return false;
    }
  }

}

