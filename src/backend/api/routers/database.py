"""
Database Query Router.

Flexible endpoints for querying any table in the recruitment database.
"""

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import asc, desc
from sqlalchemy.orm import joinedload

from src.backend.api.schemas.database import (
    TableName,
    SortOrder,
    QueryRequest,
    QueryResponse,
    SingleRecordResponse,
)
from src.backend.database.candidates.client import SessionLocal
from src.backend.database.candidates.models import (
    Candidate,
    CVScreeningResult,
    VoiceScreeningResult,
    InterviewScheduling,
    FinalDecision,
)


router = APIRouter()


# ==================================================================================
# TABLE MAPPING
# ==================================================================================

TABLE_MAP = {
    TableName.candidates: Candidate,
    TableName.cv_screening_results: CVScreeningResult,
    TableName.voice_screening_results: VoiceScreeningResult,
    TableName.interview_scheduling: InterviewScheduling,
    TableName.final_decision: FinalDecision,
}


# ==================================================================================
# HELPER FUNCTIONS
# ==================================================================================

def model_to_dict(obj: Any, fields: Optional[list[str]] = None) -> dict[str, Any]:
    """
    Convert a SQLAlchemy model instance to a dictionary.
    
    Args:
        obj: SQLAlchemy model instance
        fields: Optional list of fields to include. If None, includes all.
        
    Returns:
        Dictionary representation of the model
    """
    if obj is None:
        return None
    
    result = {}
    for column in obj.__table__.columns:
        key = column.name
        if fields is None or key in fields:
            value = getattr(obj, key)
            # Convert UUID and Enum to string for JSON serialization
            if hasattr(value, 'hex'):  # UUID
                value = str(value)
            elif hasattr(value, 'value'):  # Enum
                value = value.value
            result[key] = value
    return result


def serialize_relation(relation_data: Any, is_list: bool = True) -> Any:
    """Serialize relationship data."""
    if relation_data is None:
        return None
    if is_list:
        return [model_to_dict(item) for item in relation_data]
    return model_to_dict(relation_data)


def apply_filters(query, model, filters: dict[str, Any]):
    """
    Apply filters to a SQLAlchemy query.
    
    Supports:
    - Simple equality: {"field": "value"}
    - Comparison operators: {"field": {"$gt": 5, "$lte": 10}}
    - List membership: {"field": {"$in": [1, 2, 3]}}
    """
    for field, value in filters.items():
        if not hasattr(model, field):
            continue
            
        column = getattr(model, field)
        
        if isinstance(value, dict):
            # Handle comparison operators
            for op, op_value in value.items():
                if op == "$eq":
                    query = query.filter(column == op_value)
                elif op == "$ne":
                    query = query.filter(column != op_value)
                elif op == "$gt":
                    query = query.filter(column > op_value)
                elif op == "$gte":
                    query = query.filter(column >= op_value)
                elif op == "$lt":
                    query = query.filter(column < op_value)
                elif op == "$lte":
                    query = query.filter(column <= op_value)
                elif op == "$in":
                    query = query.filter(column.in_(op_value))
                elif op == "$nin":
                    query = query.filter(~column.in_(op_value))
                elif op == "$like":
                    query = query.filter(column.like(op_value))
                elif op == "$ilike":
                    query = query.filter(column.ilike(op_value))
        else:
            # Simple equality
            query = query.filter(column == value)
    
    return query


# ==================================================================================
# ENDPOINTS
# ==================================================================================

@router.post("/query", response_model=QueryResponse)
async def query_table(request: QueryRequest) -> QueryResponse:
    """
    Flexible query endpoint for any table.
    
    Supports filtering, field selection, pagination, and sorting.
    
    Example request body:
    ```json
    {
        "table": "candidates",
        "filters": {"status": "applied"},
        "fields": ["id", "full_name", "email"],
        "limit": 10,
        "offset": 0,
        "sort_by": "created_at",
        "sort_order": "desc"
    }
    ```
    """
    model = TABLE_MAP.get(request.table)
    if not model:
        raise HTTPException(status_code=400, detail=f"Unknown table: {request.table}")
    
    try:
        with SessionLocal() as session:
            # Base query
            query = session.query(model)
            
            # Apply eager loading for relations if requested (candidates only)
            if request.include_relations and request.table == TableName.candidates:
                query = query.options(
                    joinedload(Candidate.cv_screening_results),
                    joinedload(Candidate.voice_screening_results),
                    joinedload(Candidate.interview_scheduling),
                    joinedload(Candidate.final_decision),
                )
            
            # Apply filters
            if request.filters:
                query = apply_filters(query, model, request.filters)
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply sorting
            if request.sort_by and hasattr(model, request.sort_by):
                sort_column = getattr(model, request.sort_by)
                if request.sort_order == SortOrder.asc:
                    query = query.order_by(asc(sort_column))
                else:
                    query = query.order_by(desc(sort_column))
            
            # Apply pagination
            query = query.offset(request.offset).limit(request.limit)
            
            # Execute query
            results = query.all()
            
            # Serialize results
            data = []
            for row in results:
                row_dict = model_to_dict(row, request.fields)
                
                # Include relations for candidates if requested
                if request.include_relations and request.table == TableName.candidates:
                    row_dict["cv_screening_results"] = serialize_relation(row.cv_screening_results)
                    row_dict["voice_screening_results"] = serialize_relation(row.voice_screening_results)
                    row_dict["interview_scheduling"] = serialize_relation(row.interview_scheduling)
                    row_dict["final_decision"] = serialize_relation(row.final_decision, is_list=False)
                
                data.append(row_dict)
            
            return QueryResponse(
                success=True,
                table=request.table.value,
                total_count=total_count,
                returned_count=len(data),
                offset=request.offset,
                data=data,
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/candidates", response_model=QueryResponse)
async def list_candidates(
    status: Optional[str] = Query(default=None, description="Filter by status"),
    limit: int = Query(default=100, ge=1, le=1000, description="Max records"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    include_relations: bool = Query(default=False, description="Include related screening data"),
) -> QueryResponse:
    """
    List all candidates with optional filtering.
    
    Convenience endpoint for the most common query.
    """
    filters = {}
    if status:
        filters["status"] = status
    
    request = QueryRequest(
        table=TableName.candidates,
        filters=filters if filters else None,
        include_relations=include_relations,
        limit=limit,
        offset=offset,
        sort_by="created_at",
        sort_order=SortOrder.desc,
    )
    return await query_table(request)


@router.get("/candidates/{candidate_id}", response_model=SingleRecordResponse)
async def get_candidate(
    candidate_id: UUID,
    include_relations: bool = Query(default=True, description="Include related screening data"),
) -> SingleRecordResponse:
    """
    Get a single candidate by ID with all related data.
    """
    try:
        with SessionLocal() as session:
            query = session.query(Candidate).filter(Candidate.id == candidate_id)
            
            if include_relations:
                query = query.options(
                    joinedload(Candidate.cv_screening_results),
                    joinedload(Candidate.voice_screening_results),
                    joinedload(Candidate.interview_scheduling),
                    joinedload(Candidate.final_decision),
                )
            
            candidate = query.first()
            
            if not candidate:
                return SingleRecordResponse(
                    success=False,
                    table="candidates",
                    data=None,
                    message=f"Candidate with ID {candidate_id} not found",
                )
            
            data = model_to_dict(candidate)
            
            if include_relations:
                data["cv_screening_results"] = serialize_relation(candidate.cv_screening_results)
                data["voice_screening_results"] = serialize_relation(candidate.voice_screening_results)
                data["interview_scheduling"] = serialize_relation(candidate.interview_scheduling)
                data["final_decision"] = serialize_relation(candidate.final_decision, is_list=False)
            
            return SingleRecordResponse(
                success=True,
                table="candidates",
                data=data,
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch candidate: {str(e)}")


@router.get("/candidates/email/{email}", response_model=SingleRecordResponse)
async def get_candidate_by_email(
    email: str,
    include_relations: bool = Query(default=True, description="Include related screening data"),
) -> SingleRecordResponse:
    """
    Get a candidate by email address.
    """
    try:
        with SessionLocal() as session:
            query = session.query(Candidate).filter(Candidate.email == email)
            
            if include_relations:
                query = query.options(
                    joinedload(Candidate.cv_screening_results),
                    joinedload(Candidate.voice_screening_results),
                    joinedload(Candidate.interview_scheduling),
                    joinedload(Candidate.final_decision),
                )
            
            candidate = query.first()
            
            if not candidate:
                return SingleRecordResponse(
                    success=False,
                    table="candidates",
                    data=None,
                    message=f"Candidate with email '{email}' not found",
                )
            
            data = model_to_dict(candidate)
            
            if include_relations:
                data["cv_screening_results"] = serialize_relation(candidate.cv_screening_results)
                data["voice_screening_results"] = serialize_relation(candidate.voice_screening_results)
                data["interview_scheduling"] = serialize_relation(candidate.interview_scheduling)
                data["final_decision"] = serialize_relation(candidate.final_decision, is_list=False)
            
            return SingleRecordResponse(
                success=True,
                table="candidates",
                data=data,
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch candidate: {str(e)}")


@router.get("/cv-screening", response_model=QueryResponse)
async def list_cv_screenings(
    candidate_id: Optional[UUID] = Query(default=None, description="Filter by candidate ID"),
    min_score: Optional[float] = Query(default=None, ge=0, le=1, description="Minimum overall fit score"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> QueryResponse:
    """
    List CV screening results with optional filtering.
    """
    filters = {}
    if candidate_id:
        filters["candidate_id"] = str(candidate_id)
    if min_score is not None:
        filters["overall_fit_score"] = {"$gte": min_score}
    
    request = QueryRequest(
        table=TableName.cv_screening_results,
        filters=filters if filters else None,
        limit=limit,
        offset=offset,
        sort_by="timestamp",
        sort_order=SortOrder.desc,
    )
    return await query_table(request)


@router.get("/voice-screening", response_model=QueryResponse)
async def list_voice_screenings(
    candidate_id: Optional[UUID] = Query(default=None, description="Filter by candidate ID"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> QueryResponse:
    """
    List voice screening results with optional filtering.
    """
    filters = {}
    if candidate_id:
        filters["candidate_id"] = str(candidate_id)
    
    request = QueryRequest(
        table=TableName.voice_screening_results,
        filters=filters if filters else None,
        limit=limit,
        offset=offset,
        sort_by="timestamp",
        sort_order=SortOrder.desc,
    )
    return await query_table(request)


@router.get("/interviews", response_model=QueryResponse)
async def list_interviews(
    candidate_id: Optional[UUID] = Query(default=None, description="Filter by candidate ID"),
    status: Optional[str] = Query(default=None, description="Filter by interview status"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> QueryResponse:
    """
    List interview scheduling records with optional filtering.
    """
    filters = {}
    if candidate_id:
        filters["candidate_id"] = str(candidate_id)
    if status:
        filters["status"] = status
    
    request = QueryRequest(
        table=TableName.interview_scheduling,
        filters=filters if filters else None,
        limit=limit,
        offset=offset,
        sort_by="start_time",
        sort_order=SortOrder.desc,
    )
    return await query_table(request)


@router.get("/decisions", response_model=QueryResponse)
async def list_decisions(
    decision: Optional[str] = Query(default=None, description="Filter by decision (e.g., 'hired', 'rejected')"),
    min_score: Optional[float] = Query(default=None, ge=0, le=1, description="Minimum overall score"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> QueryResponse:
    """
    List final decisions with optional filtering.
    """
    filters = {}
    if decision:
        filters["decision"] = decision
    if min_score is not None:
        filters["overall_score"] = {"$gte": min_score}
    
    request = QueryRequest(
        table=TableName.final_decision,
        filters=filters if filters else None,
        limit=limit,
        offset=offset,
        sort_by="timestamp",
        sort_order=SortOrder.desc,
    )
    return await query_table(request)


@router.get("/stats")
async def get_database_stats() -> dict:
    """
    Get summary statistics for all tables.
    """
    try:
        with SessionLocal() as session:
            stats = {
                "candidates": {
                    "total": session.query(Candidate).count(),
                },
                "cv_screening_results": {
                    "total": session.query(CVScreeningResult).count(),
                },
                "voice_screening_results": {
                    "total": session.query(VoiceScreeningResult).count(),
                },
                "interview_scheduling": {
                    "total": session.query(InterviewScheduling).count(),
                },
                "final_decision": {
                    "total": session.query(FinalDecision).count(),
                },
            }
            
            # Get candidate status breakdown
            from sqlalchemy import func
            status_counts = session.query(
                Candidate.status, func.count(Candidate.id)
            ).group_by(Candidate.status).all()
            
            stats["candidates"]["by_status"] = {
                str(status.value) if hasattr(status, 'value') else str(status): count 
                for status, count in status_counts
            }
            
            return {"success": True, "stats": stats}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/health")
async def database_health():
    """Health check for database router."""
    try:
        with SessionLocal() as session:
            # Simple connectivity check
            from sqlalchemy import text
            session.execute(text("SELECT 1"))
        return {"status": "healthy", "service": "database", "connection": "ok"}
    except Exception as e:
        return {"status": "unhealthy", "service": "database", "error": str(e)}

