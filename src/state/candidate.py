import enum

class CandidateStatus(str, enum.Enum):
    """
    Application proces and status updates
    -------------------------------------
    1) CV Upload 
        -> "applied"

    2) CV Screening
        -> "cv_screened"
        -> "cv_passed"
        -> "cv_rejected"

    3) Voice Screening Invitation
        -> "voice_invitation_sent"

    4) Voice Screening
        -> "voice_screened"
              & "voice_passed" 
              OR "voice_rejected"
    """
    applied = "applied"
    cv_screened = "cv_screened"
    cv_passed = "cv_passed"
    cv_rejected = "cv_rejected"
    voice_invitation_sent = "voice_invitation_sent"
    voice_done = "voice_done"
    voice_passed = "voice_passed"
    voice_rejected = "voice_rejected"
    interview_scheduled = "interview_scheduled"
    decision_made = "decision_made"


class InterviewStatus(str, enum.Enum):
    """
    Person-to-Person Interview
    -------------------------------------
    5) Interview Scheduling
        -> "interview_scheduled"
        -> "interview_completed"
        -> "interview_cancelled"

        -> "interview_passed"
        -> "interview_rejected"
    """
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"
    passed = "passed"
    rejected = "rejected"


class DecisionStatus(str, enum.Enum):
    """
    Final Decision
    -------------------------------------
    6) Decision Made
        -> "hired"
        -> "rejected"
        -> "pending"
    """
    hired = "hired"
    rejected = "rejected"
    pending = "pending"