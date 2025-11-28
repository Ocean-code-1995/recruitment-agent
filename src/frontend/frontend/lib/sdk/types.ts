/**
 * TypeScript types for the Recruitment Agent SDK.
 * These types mirror the Python SDK dataclasses.
 */

// Supervisor Client Types
export interface ChatResponse {
  content: string;
  thread_id: string;
  token_count: number;
}

export interface StreamChunk {
  type: 'token' | 'done' | 'error';
  content?: string;
  thread_id?: string;
  token_count?: number;
  error?: string;
}

export interface NewChatResponse {
  thread_id: string;
  message: string;
}

// Database Client Types
export interface QueryResponse {
  success: boolean;
  table: string;
  total_count: number;
  returned_count: number;
  offset: number;
  data: Array<Record<string, any>>;
  message?: string;
}

export interface SingleRecordResponse {
  success: boolean;
  table: string;
  data?: Record<string, any>;
  message?: string;
}

export interface StatsResponse {
  success: boolean;
  stats: Record<string, any>;
}

// CV Upload Client Types
export interface SubmitResponse {
  success: boolean;
  message: string;
  candidate_name?: string;
  email?: string;
  cv_file_path?: string;
  already_exists?: boolean;
}

// Health Check Response
export interface HealthResponse {
  status: string;
  service?: string;
  connection?: string;
  error?: string;
}

