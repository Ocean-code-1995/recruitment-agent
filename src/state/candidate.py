import enum

class CandidateStatus(str, enum.Enum):
    applied = "applied"
    cv_screened = "cv_screened"
    voice_done = "voice_done"
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