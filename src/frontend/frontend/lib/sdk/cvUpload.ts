/**
 * CV Upload API Client
 * 
 * A TypeScript client for submitting job applications with CV uploads.
 * This mirrors the Python SDK's CVUploadClient functionality.
 */

import { getBaseUrl } from './config';
import { SubmitResponse } from './types';

export class CVUploadClient {
  private baseUrl: string;

  /**
   * Initialize the CV Upload client.
   * 
   * @param baseUrl Optional API base URL. Defaults to CV_UPLOAD_API_URL env var
   *                or http://localhost:8080/api/v1/cv
   */
  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || getBaseUrl('cv');
  }

  /**
   * Submit a job application with CV.
   * 
   * @param fullName Candidate's full name
   * @param email Candidate's email address
   * @param cvFile File object containing the CV (PDF or DOCX)
   * @param filename Original filename of the CV
   * @param phone Optional phone number
   * @param timeout Request timeout in milliseconds (default: 120000)
   * @returns SubmitResponse with success status and details
   */
  async submit(
    fullName: string,
    email: string,
    cvFile: File,
    filename: string,
    phone: string = '',
    timeout: number = 120000
  ): Promise<SubmitResponse> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const formData = new FormData();
      formData.append('full_name', fullName);
      formData.append('email', email);
      formData.append('phone', phone);
      formData.append('cv_file', cvFile, filename);

      const response = await fetch(`${this.baseUrl}/submit`, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
        // Don't set Content-Type header - browser will set it automatically with boundary for FormData
      });

      clearTimeout(timeoutId);

      if (response.status === 400) {
        const error = await response.json().catch(() => ({ detail: 'Invalid request' }));
        throw new Error(`Validation error: ${error.detail || 'Invalid request'}`);
      }

      if (response.status === 500) {
        const error = await response.json().catch(() => ({ detail: 'Server error' }));
        throw new Error(`Server error: ${error.detail || 'Server error'}`);
      }

      if (!response.ok) {
        throw new Error(`Unexpected status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.success,
        message: data.message,
        candidate_name: data.candidate_name || '',
        email: data.email || '',
        cv_file_path: data.cv_file_path || '',
        already_exists: data.already_exists || false,
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

