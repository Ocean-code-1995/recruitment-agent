"""
Supervisor Agent for HR Recruitment Workflow

Implements full context engineering strategy from supervisor.md:
1. Adaptive re-planning based on subagent outputs
2. Stateless subagent handling with context injection
3. Lightweight reflection/summary generation after each step
4. Candidate-specific state file management
5. Tool call logging and error tracking
6. Memory compaction to prevent context pollution
7. Retry logic for failures
8. Dashboard trace generation

Reference: docs/agents/supervisor.md
"""

import json
import tempfile
from typing import Optional, Any, Dict, List
from enum import Enum
from pathlib import Path
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

from src.agents.cv_screening.screener import evaluate_cv
from src.agents.cv_screening.schemas.output_schema import CVScreeningOutput
from src.state.candidate import CandidateStatus, DecisionStatus


# ============================================================================
# 1. WORKFLOW STAGE DEFINITIONS
# ============================================================================

class WorkflowStage(str, Enum):
    """Stages of the HR recruitment workflow"""
    CV_SCREENING = "cv_screening"
    VOICE_SCREENING = "voice_screening"
    HR_SCHEDULING = "hr_scheduling"
    DECISION = "decision"
    COMPLETE = "complete"


# ============================================================================
# 2. CONTEXT ENGINEERING - MEMORY SUMMARIES
# ============================================================================

class StageSummary(BaseModel):
    """Compacted output from a completed stage (context engineering)"""
    stage: WorkflowStage
    timestamp: str
    success: bool
    summary: str  # High-level summary, not full output
    key_metrics: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class CandidateMemoryContext(BaseModel):
    """Candidate-specific state loaded for each task (stateless approach)"""
    candidate_id: str
    candidate_email: str
    cv_text: Optional[str] = None
    jd_text: Optional[str] = None
    stage_summaries: List[StageSummary] = Field(default_factory=list)  # Compacted history
    tool_call_log: List[Dict[str, Any]] = Field(default_factory=list)  # Tool execution history
    human_checkpoint_required: bool = False
    human_checkpoint_notes: Optional[str] = None


class WorkflowPlan(BaseModel):
    """Represents the supervisor's workflow plan"""
    candidate_id: str
    current_stage: WorkflowStage = Field(default=WorkflowStage.CV_SCREENING)
    completed_stages: List[WorkflowStage] = Field(default_factory=list)
    pending_stages: List[WorkflowStage] = Field(
        default_factory=lambda: [
            WorkflowStage.VOICE_SCREENING,
            WorkflowStage.HR_SCHEDULING,
            WorkflowStage.DECISION,
        ]
    )
    adaptive_notes: str = Field(default="")
    retry_count: int = 0
    max_retries: int = 2


# ============================================================================
# 3. SUBAGENT RESULT CONTRACTS
# ============================================================================

class SubagentResult(BaseModel):
    """Standardized output from any subagent"""
    stage: WorkflowStage
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    requires_human_review: bool = False


# ============================================================================
# 4. TOOL CALL LOGGING (for trace and error recovery)
# ============================================================================

class ToolCallRecord(BaseModel):
    """Records each tool invocation for debugging and replay"""
    timestamp: str
    tool_name: str
    stage: WorkflowStage
    input_args: Dict[str, Any]
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_attempt: int = 0


# ============================================================================
# 5. REAL CV SCREENING (only implemented agent)
# ============================================================================

def invoke_cv_screening_agent(
    cv_text: str,
    jd_text: str,
    candidate_id: str,
    tool_log: List[ToolCallRecord],
) -> SubagentResult:
    """
    Invoke CV Screening Agent (REAL implementation via evaluate_cv).
    
    Args:
        cv_text: Candidate's CV
        jd_text: Job description
        candidate_id: For logging
        tool_log: Tool call history
    
    Returns:
        SubagentResult with structured output
    """
    record = ToolCallRecord(
        timestamp=datetime.now().isoformat(),
        tool_name="cv_screening_agent",
        stage=WorkflowStage.CV_SCREENING,
        input_args={"candidate_id": candidate_id},
    )
    
    try:
        cv_output = evaluate_cv(cv_text, jd_text)
        
        record.output = cv_output.model_dump()
        tool_log.append(record)
        
        return SubagentResult(
            stage=WorkflowStage.CV_SCREENING,
            success=True,
            data={
                "overall_fit_score": cv_output.overall_fit_score,
                "skills_match_score": cv_output.skills_match_score,
                "experience_match_score": cv_output.experience_match_score,
                "education_match_score": cv_output.education_match_score,
                "llm_feedback": cv_output.llm_feedback,
            },
        )
    except Exception as e:
        record.error = str(e)
        tool_log.append(record)
        return SubagentResult(
            stage=WorkflowStage.CV_SCREENING,
            success=False,
            data={},
            error=str(e),
        )


# ============================================================================
# 6. DUMMY SUBAGENTS (TODO: implement when ready)
# ============================================================================

def invoke_voice_screening_agent(
    candidate_id: str,
    candidate_email: str,
    tool_log: List[ToolCallRecord],
) -> SubagentResult:
    """TODO: Voice Screening Agent - not yet implemented"""
    record = ToolCallRecord(
        timestamp=datetime.now().isoformat(),
        tool_name="voice_screening_agent",
        stage=WorkflowStage.VOICE_SCREENING,
        input_args={"candidate_id": candidate_id},
        error="Not yet implemented",
    )
    tool_log.append(record)
    
    return SubagentResult(
        stage=WorkflowStage.VOICE_SCREENING,
        success=False,
        data={},
        error="TODO: Voice Screening Agent not yet implemented",
    )


def invoke_scheduler_agent(
    candidate_id: str,
    candidate_email: str,
    tool_log: List[ToolCallRecord],
) -> SubagentResult:
    """TODO: HR Scheduling Agent - not yet implemented"""
    record = ToolCallRecord(
        timestamp=datetime.now().isoformat(),
        tool_name="scheduler_agent",
        stage=WorkflowStage.HR_SCHEDULING,
        input_args={"candidate_id": candidate_id},
        error="Not yet implemented",
    )
    tool_log.append(record)
    
    return SubagentResult(
        stage=WorkflowStage.HR_SCHEDULING,
        success=False,
        data={},
        error="TODO: HR Scheduling Agent not yet implemented",
    )


def invoke_decision_agent(
    candidate_id: str,
    memory_context: CandidateMemoryContext,
    tool_log: List[ToolCallRecord],
) -> SubagentResult:
    """TODO: Decision Agent - not yet implemented"""
    record = ToolCallRecord(
        timestamp=datetime.now().isoformat(),
        tool_name="decision_agent",
        stage=WorkflowStage.DECISION,
        input_args={"candidate_id": candidate_id},
        error="Not yet implemented",
    )
    tool_log.append(record)
    
    return SubagentResult(
        stage=WorkflowStage.DECISION,
        success=False,
        data={},
        error="TODO: Decision Agent not yet implemented",
    )


# ============================================================================
# 7. CONTEXT ENGINEERING - REFLECTION & SUMMARY GENERATION
# ============================================================================

def generate_stage_summary(result: SubagentResult) -> StageSummary:
    """
    Generate lightweight reflection summary after subagent execution.
    This compacts the output to prevent context pollution.
    
    Args:
        result: The subagent's result
    
    Returns:
        StageSummary: Compacted version of the result
    """
    if result.stage == WorkflowStage.CV_SCREENING:
        return StageSummary(
            stage=result.stage,
            timestamp=datetime.now().isoformat(),
            success=result.success,
            summary=f"CV score: {result.data.get('overall_fit_score', 'N/A'):.2f} - {result.data.get('llm_feedback', 'N/A')[:100]}...",
            key_metrics={
                "overall_fit_score": result.data.get("overall_fit_score"),
                "skills_match": result.data.get("skills_match_score"),
                "experience_match": result.data.get("experience_match_score"),
            },
        )
    
    return StageSummary(
        stage=result.stage,
        timestamp=datetime.now().isoformat(),
        success=result.success,
        summary=f"Stage {result.stage.value}: {'Success' if result.success else 'Failed'}",
        key_metrics=result.data,
    )


# ============================================================================
# 8. SUPERVISOR AGENT - MAIN ORCHESTRATOR
# ============================================================================

class HRSupervisor:
    """
    Supervisor Agent that orchestrates the HR recruitment workflow.
    
    Implements full context engineering strategy:
    1. Adaptive re-planning based on subagent outputs
    2. Stateless subagent handling with context injection
    3. Reflection/summary generation
    4. Candidate-specific state files
    5. Tool call logging
    6. Memory compaction
    7. Retry logic
    8. Dashboard trace generation
    """
    
    def __init__(self):
        self.model = ChatOpenAI(model="gpt-4o", temperature=0.7)
        self.temp_dir = Path(tempfile.gettempdir())
    
    # ========================================================================
    # 1. PLAN INITIALIZATION
    # ========================================================================
    
    def initialize_plan(
        self,
        candidate_id: str,
        candidate_email: str,
        cv_text: str,
        jd_text: str,
    ) -> tuple[WorkflowPlan, CandidateMemoryContext]:
        """
        Initialize workflow plan for a candidate.
        
        Args:
            candidate_id: Unique candidate identifier
            candidate_email: Candidate email
            cv_text: Candidate's CV
            jd_text: Job description
        
        Returns:
            Tuple of (WorkflowPlan, CandidateMemoryContext)
        """
        plan = WorkflowPlan(
            candidate_id=candidate_id,
            current_stage=WorkflowStage.CV_SCREENING,
        )
        
        memory = CandidateMemoryContext(
            candidate_id=candidate_id,
            candidate_email=candidate_email,
            cv_text=cv_text,
            jd_text=jd_text,
        )
        
        return plan, memory
    
    # ========================================================================
    # 2. EXECUTE NEXT STAGE (with context injection)
    # ========================================================================
    
    def execute_next_stage(
        self,
        plan: WorkflowPlan,
        memory: CandidateMemoryContext,
    ) -> SubagentResult:
        """
        Execute the next stage in the workflow.
        Injects only relevant context to the subagent (stateless approach).
        
        Args:
            plan: Current workflow plan
            memory: Candidate memory context
        
        Returns:
            SubagentResult from the executed stage
        """
        stage = plan.current_stage
        
        if stage == WorkflowStage.CV_SCREENING:
            return invoke_cv_screening_agent(
                memory.cv_text,
                memory.jd_text,
                memory.candidate_id,
                memory.tool_call_log,
            )
        elif stage == WorkflowStage.VOICE_SCREENING:
            return invoke_voice_screening_agent(
                memory.candidate_id,
                memory.candidate_email,
                memory.tool_call_log,
            )
        elif stage == WorkflowStage.HR_SCHEDULING:
            return invoke_scheduler_agent(
                memory.candidate_id,
                memory.candidate_email,
                memory.tool_call_log,
            )
        elif stage == WorkflowStage.DECISION:
            return invoke_decision_agent(
                memory.candidate_id,
                memory,
                memory.tool_call_log,
            )
        else:
            return SubagentResult(
                stage=stage,
                success=False,
                data={},
                error=f"Unknown stage: {stage}",
            )
    
    # ========================================================================
    # 3. REFLECT & GENERATE SUMMARY (context engineering)
    # ========================================================================
    
    def reflect_and_summarize(
        self,
        result: SubagentResult,
        memory: CandidateMemoryContext,
    ) -> str:
        """
        Perform lightweight reflection after subagent execution.
        Generates summary to prevent context pollution.
        
        Args:
            result: The subagent result
            memory: Candidate memory context
        
        Returns:
            Reflection text for adaptive planning
        """
        summary = generate_stage_summary(result)
        memory.stage_summaries.append(summary)
        
        reflection = (
            f"Stage {result.stage.value} completed: {'SUCCESS' if result.success else 'FAILED'}\n"
            f"Summary: {summary.summary}\n"
        )
        
        if result.error:
            reflection += f"Error: {result.error}\n"
        
        return reflection
    
    # ========================================================================
    # 4. ADAPTIVE RE-PLANNING
    # ========================================================================
    
    def adapt_plan(
        self,
        plan: WorkflowPlan,
        result: SubagentResult,
        reflection: str,
    ) -> None:
        """
        Adaptively update the workflow plan based on subagent results.
        Implements decision rules from supervisor.md.
        
        Args:
            plan: Current workflow plan
            result: SubagentResult from the executed stage
            reflection: Reflection text
        """
        plan.completed_stages.append(result.stage)
        
        if result.stage == WorkflowStage.CV_SCREENING:
            cv_score = result.data.get("overall_fit_score", 0)
            
            if cv_score < 0.4:
                # Low score: skip voice/scheduling, go to rejection
                plan.pending_stages = [WorkflowStage.DECISION]
                plan.adaptive_notes += f"\nCV score {cv_score:.2f} too low - skipping voice and scheduling"
            elif cv_score < 0.6:
                # Marginal score: skip voice screening
                if WorkflowStage.VOICE_SCREENING in plan.pending_stages:
                    plan.pending_stages.remove(WorkflowStage.VOICE_SCREENING)
                plan.adaptive_notes += f"\nCV score {cv_score:.2f} marginal - skipping voice screening"
            else:
                # Strong score: proceed normally
                plan.adaptive_notes += f"\nCV score {cv_score:.2f} strong - proceeding to voice screening"
        
        elif result.stage == WorkflowStage.VOICE_SCREENING:
            if not result.success:
                plan.adaptive_notes += "\nVoice screening failed - manual review recommended"
                plan.human_checkpoint_required = True
        
        elif result.stage == WorkflowStage.HR_SCHEDULING:
            if not result.success:
                plan.adaptive_notes += "\nScheduling constraints detected - alternative times needed"
                plan.human_checkpoint_required = True
        
        # Move to next stage
        if plan.pending_stages:
            plan.current_stage = plan.pending_stages[0]
        else:
            plan.current_stage = WorkflowStage.COMPLETE
    
    # ========================================================================
    # 5. RETRY LOGIC (error handling)
    # ========================================================================
    
    def should_retry(self, plan: WorkflowPlan, result: SubagentResult) -> bool:
        """
        Determine if a failed stage should be retried.
        
        Args:
            plan: Current workflow plan
            result: SubagentResult
        
        Returns:
            True if should retry, False otherwise
        """
        if result.success:
            return False
        
        if plan.retry_count >= plan.max_retries:
            return False
        
        # Retry transient errors (e.g., tool failures)
        if "TODO" in result.error or "not yet implemented" in result.error:
            return False  # Don't retry unimplemented features
        
        return True
    
    # ========================================================================
    # 6. CANDIDATE STATE PERSISTENCE (TODO format)
    # ========================================================================
    
    def save_candidate_state(
        self,
        plan: WorkflowPlan,
        memory: CandidateMemoryContext,
    ) -> Path:
        """
        Save candidate-specific state to temporary file.
        
        Args:
            plan: Current workflow plan
            memory: Candidate memory context
        
        Returns:
            Path to state file
        """
        state_file = self.temp_dir / f"candidate_{plan.candidate_id}_state.json"
        
        state_data = {
            "plan": plan.model_dump(),
            "memory": memory.model_dump(),
        }
        
        state_file.write_text(json.dumps(state_data, indent=2, default=str))
        return state_file
    
    def load_candidate_state(
        self,
        candidate_id: str,
    ) -> Optional[tuple[WorkflowPlan, CandidateMemoryContext]]:
        """
        Load candidate-specific state from file.
        
        Args:
            candidate_id: Candidate identifier
        
        Returns:
            Tuple of (plan, memory) or None if not found
        """
        state_file = self.temp_dir / f"candidate_{candidate_id}_state.json"
        
        if not state_file.exists():
            return None
        
        state_data = json.loads(state_file.read_text())
        plan = WorkflowPlan(**state_data["plan"])
        memory = CandidateMemoryContext(**state_data["memory"])
        
        return plan, memory
    
    def cleanup_candidate_state(self, candidate_id: str) -> None:
        """Delete candidate state file (called when hiring decision made)."""
        state_file = self.temp_dir / f"candidate_{candidate_id}_state.json"
        if state_file.exists():
            state_file.unlink()
    
    # ========================================================================
    # 7. MAIN WORKFLOW EXECUTOR
    # ========================================================================
    
    def run_workflow(
        self,
        candidate_id: str,
        candidate_email: str,
        cv_text: str,
        jd_text: str,
    ) -> Dict[str, Any]:
        """
        Execute complete workflow for a candidate.
        
        Args:
            candidate_id: Unique candidate ID
            candidate_email: Candidate email
            cv_text: Candidate's CV
            jd_text: Job description
        
        Returns:
            Dictionary with final results and traces
        """
        plan, memory = self.initialize_plan(
            candidate_id,
            candidate_email,
            cv_text,
            jd_text,
        )
        
        while plan.current_stage != WorkflowStage.COMPLETE:
            # Execute stage
            result = self.execute_next_stage(plan, memory)
            
            # Reflect and summarize
            reflection = self.reflect_and_summarize(result, memory)
            
            # Adaptive re-planning
            self.adapt_plan(plan, result, reflection)
            
            # Retry if needed
            if self.should_retry(plan, result):
                plan.retry_count += 1
                continue
            
            # Save state
            self.save_candidate_state(plan, memory)
        
        # Generate final trace
        trace = self.get_reasoning_trace(plan, memory)
        
        # Cleanup state file
        self.cleanup_candidate_state(candidate_id)
        
        return trace
    
    # ========================================================================
    # 8. DASHBOARD TRACE GENERATION
    # ========================================================================
    
    def get_reasoning_trace(
        self,
        plan: WorkflowPlan,
        memory: CandidateMemoryContext,
    ) -> Dict[str, Any]:
        """
        Generate structured trace for dashboard visualization.
        Includes plan state, memory summaries, tool logs, and reasoning.
        
        Args:
            plan: Current workflow plan
            memory: Candidate memory context
        
        Returns:
            Structured trace dictionary
        """
        return {
            "candidate_id": memory.candidate_id,
            "plan": {
                "current_stage": plan.current_stage.value,
                "completed_stages": [s.value for s in plan.completed_stages],
                "pending_stages": [s.value for s in plan.pending_stages],
            },
            "memory_summaries": [
                {
                    "stage": s.stage.value,
                    "timestamp": s.timestamp,
                    "success": s.success,
                    "summary": s.summary,
                    "key_metrics": s.key_metrics,
                }
                for s in memory.stage_summaries
            ],
            "tool_calls": [
                {
                    "timestamp": tc.timestamp,
                    "tool_name": tc.tool_name,
                    "stage": tc.stage.value,
                    "error": tc.error,
                }
                for tc in memory.tool_call_log
            ],
            "adaptive_notes": plan.adaptive_notes,
            "human_checkpoint_required": plan.human_checkpoint_required,
            "human_checkpoint_notes": plan.human_checkpoint_notes,
        }