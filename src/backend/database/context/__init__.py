from sqlalchemy import (
    Column, String, Integer, Float, Enum, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import enum
import uuid

Base = declarative_base()


# ==============================================================
# ENUM DEFINITIONS
# ==============================================================

class CandidateStatus(enum.Enum):
    APPLIED = "applied"
    CV_SCREENED = "cv_screened"
    INVITED_VOICE = "invited_voice"
    VOICE_DONE = "voice_done"
    SCHEDULED_HR = "scheduled_hr"
    DECISION_PENDING = "decision_pending"
    REJECTED = "rejected"
    HIRED = "hired"


class InterviewStatus(enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Decision(enum.Enum):
    HIRE = "hire"
    REJECT = "reject"
    MAYBE = "maybe"


# ==============================================================
# MAIN TABLES
# ==============================================================

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    phone_number = Column(String(50), nullable=True)
    cv_file_path = Column(String(500), nullable=True)
    parsed_cv_json = Column(JSON, nullable=True)
    status = Column(Enum(CandidateStatus), default=CandidateStatus.APPLIED)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    cv_results = relationship("CVScreeningResult", back_populates="candidate", cascade="all, delete-orphan")
    voice_results = relationship("VoiceScreeningResult", back_populates="candidate", cascade="all, delete-orphan")
    interviews = relationship("InterviewScheduling", back_populates="candidate", cascade="all, delete-orphan")
    decision = relationship("FinalDecision", back_populates="candidate", uselist=False, cascade="all, delete-orphan")


# ==============================================================
# CV SCREENING RESULTS
# ==============================================================

class CVScreeningResult(Base):
    __tablename__ = "cv_screening_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)
    job_title = Column(String(255), nullable=True)

    skills_match_score = Column(Float, nullable=True)
    experience_match_score = Column(Float, nullable=True)
    education_match_score = Column(Float, nullable=True)
    overall_fit_score = Column(Float, nullable=True)

    llm_feedback = Column(Text, nullable=True)
    reasoning_trace = Column(JSON, nullable=True)

    timestamp = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="cv_results")


# ==============================================================
# VOICE SCREENING RESULTS
# ==============================================================

class VoiceScreeningResult(Base):
    __tablename__ = "voice_screening_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)

    call_sid = Column(String(255), nullable=True)
    transcript_text = Column(Text, nullable=True)

    sentiment_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    communication_score = Column(Float, nullable=True)

    llm_summary = Column(Text, nullable=True)
    llm_judgment_json = Column(JSON, nullable=True)
    audio_url = Column(String(500), nullable=True)

    timestamp = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="voice_results")


# ==============================================================
# INTERVIEW SCHEDULING
# ==============================================================

class InterviewScheduling(Base):
    __tablename__ = "interview_scheduling"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)

    calendar_event_id = Column(String(255), nullable=True)
    event_summary = Column(String(255), nullable=True)

    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    status = Column(Enum(InterviewStatus), default=InterviewStatus.SCHEDULED)

    timestamp = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="interviews")


# ==============================================================
# FINAL DECISION
# ==============================================================

class FinalDecision(Base):
    __tablename__ = "final_decision"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False, unique=True)

    overall_score = Column(Float, nullable=True)
    decision = Column(Enum(Decision), default=Decision.MAYBE)
    llm_rationale = Column(Text, nullable=True)
    human_notes = Column(Text, nullable=True)

    timestamp = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="decision")
