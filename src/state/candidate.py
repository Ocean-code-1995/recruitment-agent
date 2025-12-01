import enum

class CandidateStatus(str, enum.Enum):
    applied = "applied"
    cv_screened = "cv_screened"
    cv_passed = "cv_passed"
    cv_rejected = "cv_rejected"
    voice_passed = "voice_passed"
    voice_rejected = "voice_rejected"
    interview_scheduled = "interview_scheduled"
    decision_made = "decision_made"


class InterviewStatus(str, enum.Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"


class DecisionStatus(str, enum.Enum):
    hire = "hire"
    reject = "reject"
    maybe = "maybe"