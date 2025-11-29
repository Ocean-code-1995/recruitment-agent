"""
Database API Client.

A client for querying the recruitment database via the API.
"""

import os
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID

import requests


def _clean_base_url(url: str) -> str:
    """Normalize base URL to avoid issues from quoted env vars."""
    cleaned = url.strip().strip("\"'")
    if cleaned.endswith("/"):
        cleaned = cleaned[:-1]
    return cleaned


@dataclass
class QueryResponse:
    """Response from a database query."""
    success: bool
    table: str
    total_count: int
    returned_count: int
    offset: int
    data: list[dict[str, Any]]
    message: Optional[str] = None


@dataclass
class SingleRecordResponse:
    """Response for a single record lookup."""
    success: bool
    table: str
    data: Optional[dict[str, Any]] = None
    message: Optional[str] = None


@dataclass
class StatsResponse:
    """Database statistics response."""
    success: bool
    stats: dict[str, Any] = field(default_factory=dict)


class DatabaseClient:
    """
    Client for the Database Query API.
    
    Usage:
        client = DatabaseClient()
        
        # Get all candidates
        response = client.get_candidates()
        for candidate in response.data:
            print(candidate["full_name"], candidate["status"])
        
        # Get candidate by email with all related data
        candidate = client.get_candidate_by_email("ada@example.com")
        if candidate.success:
            print(candidate.data["cv_screening_results"])
        
        # Flexible query with filters
        response = client.query(
            table="candidates",
            filters={"status": "applied"},
            fields=["id", "full_name", "email"],
            limit=10
        )
        
        # Get CV screening results with score filter
        screenings = client.get_cv_screenings(min_score=0.8)
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the Database client.
        
        Args:
            base_url: API base URL. Defaults to DATABASE_API_URL env var
                      or http://localhost:8080/api/v1/db
        """
        raw = base_url or os.getenv(
            "DATABASE_API_URL",
            "http://localhost:8080/api/v1/db"
        )
        self.base_url = _clean_base_url(raw)
        self.timeout = 30
    
    # ==================================================================================
    # FLEXIBLE QUERY
    # ==================================================================================
    
    def query(
        self,
        table: str,
        filters: Optional[dict[str, Any]] = None,
        fields: Optional[list[str]] = None,
        include_relations: bool = False,
        limit: int = 100,
        offset: int = 0,
        sort_by: Optional[str] = None,
        sort_order: str = "desc"
    ) -> QueryResponse:
        """
        Flexible query for any table.
        
        Args:
            table: Table name (candidates, cv_screening_results, voice_screening_results, 
                   interview_scheduling, final_decision)
            filters: Key-value filters. Supports operators like {"field": {"$gte": 0.8}}
            fields: Specific fields to return. None returns all.
            include_relations: Include related data (candidates table only)
            limit: Max records to return
            offset: Number of records to skip
            sort_by: Field to sort by
            sort_order: "asc" or "desc"
            
        Returns:
            QueryResponse with data and pagination info
        """
        payload = {
            "table": table,
            "filters": filters,
            "fields": fields,
            "include_relations": include_relations,
            "limit": limit,
            "offset": offset,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }
        
        response = requests.post(
            f"{self.base_url}/query",
            json=payload,
            timeout=self.timeout
        )
        self._handle_error(response)
        
        data = response.json()
        return QueryResponse(
            success=data["success"],
            table=data["table"],
            total_count=data["total_count"],
            returned_count=data["returned_count"],
            offset=data["offset"],
            data=data["data"],
            message=data.get("message"),
        )
    
    # ==================================================================================
    # CANDIDATES
    # ==================================================================================
    
    def get_candidates(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        include_relations: bool = False
    ) -> QueryResponse:
        """
        List all candidates with optional filtering.
        
        Args:
            status: Filter by status (e.g., "applied", "screening", "interviewed")
            limit: Max records to return
            offset: Pagination offset
            include_relations: Include CV/voice screening results, interviews, decisions
            
        Returns:
            QueryResponse with candidate data
        """
        params = {
            "limit": limit,
            "offset": offset,
            "include_relations": include_relations,
        }
        if status:
            params["status"] = status
        
        response = requests.get(
            f"{self.base_url}/candidates",
            params=params,
            timeout=self.timeout
        )
        self._handle_error(response)
        
        data = response.json()
        return QueryResponse(
            success=data["success"],
            table=data["table"],
            total_count=data["total_count"],
            returned_count=data["returned_count"],
            offset=data["offset"],
            data=data["data"],
            message=data.get("message"),
        )
    
    def get_candidate(
        self,
        candidate_id: str | UUID,
        include_relations: bool = True
    ) -> SingleRecordResponse:
        """
        Get a single candidate by ID with all related data.
        
        Args:
            candidate_id: Candidate UUID
            include_relations: Include CV/voice screening, interviews, decisions
            
        Returns:
            SingleRecordResponse with full candidate profile
        """
        response = requests.get(
            f"{self.base_url}/candidates/{candidate_id}",
            params={"include_relations": include_relations},
            timeout=self.timeout
        )
        self._handle_error(response)
        
        data = response.json()
        return SingleRecordResponse(
            success=data["success"],
            table=data["table"],
            data=data.get("data"),
            message=data.get("message"),
        )
    
    def get_candidate_by_email(
        self,
        email: str,
        include_relations: bool = True
    ) -> SingleRecordResponse:
        """
        Get a candidate by email address with all related data.
        
        Args:
            email: Candidate's email address
            include_relations: Include CV/voice screening, interviews, decisions
            
        Returns:
            SingleRecordResponse with full candidate profile
        """
        response = requests.get(
            f"{self.base_url}/candidates/email/{email}",
            params={"include_relations": include_relations},
            timeout=self.timeout
        )
        self._handle_error(response)
        
        data = response.json()
        return SingleRecordResponse(
            success=data["success"],
            table=data["table"],
            data=data.get("data"),
            message=data.get("message"),
        )
    
    # ==================================================================================
    # CV SCREENING
    # ==================================================================================
    
    def get_cv_screenings(
        self,
        candidate_id: Optional[str | UUID] = None,
        min_score: Optional[float] = None,
        limit: int = 100,
        offset: int = 0
    ) -> QueryResponse:
        """
        List CV screening results.
        
        Args:
            candidate_id: Filter by candidate
            min_score: Minimum overall fit score (0.0 - 1.0)
            limit: Max records
            offset: Pagination offset
            
        Returns:
            QueryResponse with CV screening results
        """
        params = {"limit": limit, "offset": offset}
        if candidate_id:
            params["candidate_id"] = str(candidate_id)
        if min_score is not None:
            params["min_score"] = min_score
        
        response = requests.get(
            f"{self.base_url}/cv-screening",
            params=params,
            timeout=self.timeout
        )
        self._handle_error(response)
        
        data = response.json()
        return QueryResponse(
            success=data["success"],
            table=data["table"],
            total_count=data["total_count"],
            returned_count=data["returned_count"],
            offset=data["offset"],
            data=data["data"],
            message=data.get("message"),
        )
    
    # ==================================================================================
    # VOICE SCREENING
    # ==================================================================================
    
    def get_voice_screenings(
        self,
        candidate_id: Optional[str | UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> QueryResponse:
        """
        List voice screening results.
        
        Args:
            candidate_id: Filter by candidate
            limit: Max records
            offset: Pagination offset
            
        Returns:
            QueryResponse with voice screening results
        """
        params = {"limit": limit, "offset": offset}
        if candidate_id:
            params["candidate_id"] = str(candidate_id)
        
        response = requests.get(
            f"{self.base_url}/voice-screening",
            params=params,
            timeout=self.timeout
        )
        self._handle_error(response)
        
        data = response.json()
        return QueryResponse(
            success=data["success"],
            table=data["table"],
            total_count=data["total_count"],
            returned_count=data["returned_count"],
            offset=data["offset"],
            data=data["data"],
            message=data.get("message"),
        )
    
    # ==================================================================================
    # INTERVIEWS
    # ==================================================================================
    
    def get_interviews(
        self,
        candidate_id: Optional[str | UUID] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> QueryResponse:
        """
        List interview scheduling records.
        
        Args:
            candidate_id: Filter by candidate
            status: Filter by interview status
            limit: Max records
            offset: Pagination offset
            
        Returns:
            QueryResponse with interview data
        """
        params = {"limit": limit, "offset": offset}
        if candidate_id:
            params["candidate_id"] = str(candidate_id)
        if status:
            params["status"] = status
        
        response = requests.get(
            f"{self.base_url}/interviews",
            params=params,
            timeout=self.timeout
        )
        self._handle_error(response)
        
        data = response.json()
        return QueryResponse(
            success=data["success"],
            table=data["table"],
            total_count=data["total_count"],
            returned_count=data["returned_count"],
            offset=data["offset"],
            data=data["data"],
            message=data.get("message"),
        )
    
    # ==================================================================================
    # DECISIONS
    # ==================================================================================
    
    def get_decisions(
        self,
        decision: Optional[str] = None,
        min_score: Optional[float] = None,
        limit: int = 100,
        offset: int = 0
    ) -> QueryResponse:
        """
        List final hiring decisions.
        
        Args:
            decision: Filter by decision (e.g., "hired", "rejected")
            min_score: Minimum overall score
            limit: Max records
            offset: Pagination offset
            
        Returns:
            QueryResponse with decision data
        """
        params = {"limit": limit, "offset": offset}
        if decision:
            params["decision"] = decision
        if min_score is not None:
            params["min_score"] = min_score
        
        response = requests.get(
            f"{self.base_url}/decisions",
            params=params,
            timeout=self.timeout
        )
        self._handle_error(response)
        
        data = response.json()
        return QueryResponse(
            success=data["success"],
            table=data["table"],
            total_count=data["total_count"],
            returned_count=data["returned_count"],
            offset=data["offset"],
            data=data["data"],
            message=data.get("message"),
        )
    
    # ==================================================================================
    # STATS & HEALTH
    # ==================================================================================
    
    def get_stats(self) -> StatsResponse:
        """
        Get database statistics.
        
        Returns:
            StatsResponse with counts for all tables and status breakdown
        """
        response = requests.get(
            f"{self.base_url}/stats",
            timeout=self.timeout
        )
        self._handle_error(response)
        
        data = response.json()
        return StatsResponse(
            success=data["success"],
            stats=data["stats"],
        )
    
    def health(self) -> bool:
        """
        Check if the database API is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200 and response.json().get("status") == "healthy"
        except requests.exceptions.RequestException:
            return False
    
    # ==================================================================================
    # HELPERS
    # ==================================================================================
    
    def _handle_error(self, response: requests.Response) -> None:
        """Raise appropriate exceptions for error responses."""
        if response.status_code == 400:
            error = response.json().get("detail", "Invalid request")
            raise ValueError(f"Validation error: {error}")
        
        if response.status_code == 500:
            error = response.json().get("detail", "Server error")
            raise ValueError(f"Server error: {error}")
        
        if response.status_code != 200:
            raise ValueError(f"Unexpected status: {response.status_code}")

