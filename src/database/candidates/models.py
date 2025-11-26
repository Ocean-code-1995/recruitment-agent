from sqlalchemy import (
    Column,
    String,
    Float,
    Text,
    DateTime,
    Enum,
    ForeignKey,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

from src.state.candidate import CandidateStatus, InterviewStatus, DecisionStatus
from src.database.candidates.utils import generate_auth_code


Base = declarative_base()


# --- TABLES ---

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone_number = Column(String)
    cv_file_path = Column(String)
    parsed_cv_file_path = Column(String)
    status = Column(Enum(CandidateStatus), default=CandidateStatus.applied, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    auth_code = Column(String, default=generate_auth_code, nullable=True)

    # Relationships
    cv_screening_results = relationship(
        "CVScreeningResult",
        back_populates="candidate",
        cascade="all, delete-orphan",
    )
    voice_screening_results = relationship(
        "VoiceScreeningResult",
        back_populates="candidate",
        cascade="all, delete-orphan",
    )
    interview_scheduling = relationship(
        "InterviewScheduling",
        back_populates="candidate",
        cascade="all, delete-orphan",
    )
    final_decision = relationship(
        "FinalDecision",
        back_populates="candidate",
        uselist=False,
        cascade="all, delete-orphan",
    )


class CVScreeningResult(Base):
    __tablename__ = "cv_screening_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    job_title = Column(String)
    skills_match_score = Column(Float)
    experience_match_score = Column(Float)
    education_match_score = Column(Float)
    overall_fit_score = Column(Float)
    llm_feedback = Column(Text)
    reasoning_trace = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="cv_screening_results")


class VoiceScreeningResult(Base):
    __tablename__ = "voice_screening_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    call_sid = Column(String)
    transcript_text = Column(Text)
    sentiment_score = Column(Float)
    confidence_score = Column(Float)
    communication_score = Column(Float)
    proficiency_score = Column(Float)
    llm_summary = Column(Text)
    llm_judgment_json = Column(JSON)
    audio_url = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="voice_screening_results")


class InterviewScheduling(Base):
    __tablename__ = "interview_scheduling"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    calendar_event_id = Column(String)
    event_summary = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(Enum(InterviewStatus))
    timestamp = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="interview_scheduling")


class FinalDecision(Base):
    __tablename__ = "final_decision"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    overall_score = Column(Float)
    decision = Column(Enum(DecisionStatus))
    llm_rationale = Column(Text)
    human_notes = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="final_decision")
