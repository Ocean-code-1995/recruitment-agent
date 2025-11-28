/**
 * SDK for interacting with Recruitment Agent APIs.
 * 
 * TypeScript/JavaScript client library that mirrors the Python SDK functionality.
 * 
 * Usage:
 * ```typescript
 * import { SupervisorClient, CVUploadClient, DatabaseClient } from '@/lib/sdk';
 * 
 * // Supervisor Agent
 * const supervisor = new SupervisorClient();
 * const response = await supervisor.chat("Show me all candidates");
 * console.log(response.content);
 * 
 * // CV Upload
 * const cvClient = new CVUploadClient();
 * const file = new File([...], "my_cv.pdf");
 * const response = await cvClient.submit(
 *   "Ada Lovelace",
 *   "ada@example.com",
 *   file,
 *   "my_cv.pdf"
 * );
 * 
 * // Database Queries
 * const db = new DatabaseClient();
 * const candidates = await db.getCandidates({ status: "applied" });
 * const candidate = await db.getCandidateByEmail("ada@example.com");
 * ```
 */

export { SupervisorClient } from './supervisor';
export { DatabaseClient } from './database';
export { CVUploadClient } from './cvUpload';
export { VoiceScreeningClient } from './voiceScreening';

export type {
  ChatResponse,
  StreamChunk,
  NewChatResponse,
  QueryResponse,
  SingleRecordResponse,
  StatsResponse,
  SubmitResponse,
  HealthResponse,
} from './types';

