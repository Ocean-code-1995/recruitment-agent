"""
Supervisor Agent for HR Recruitment Workflow

Implements full context engineering strategy from supervisor.md with 
LLM-DRIVEN AUTONOMOUS DECISION-MAKING:

Key principles:
1. All decisions are made by LLM reasoning, NOT hardcoded rules
2. Supervisor has tools it can invoke; the LLM decides when/how to use them
3. No hardcoded stage sequence - LLM autonomously chooses workflow
4. Context engineering prevents token bloat and improves reliability
5. Transparent tool call logging for dashboard tracing

The supervisor operates as an agentic loop:
- LLM receives candidate context and tool descriptions
- LLM autonomously decides which tool (agent) to invoke
- Tools provide structured results back to LLM
- LLM reasons about results and decides what to do next
- Loop continues until LLM signals workflow complete

Reference: docs/agents/supervisor.md
Reference: https://github.com/langchain-ai/langgraph-supervisor-py/blob/main/README.md
"""

import json
import tempfile
from typing import Optional, Any, Dict, List
from enum import Enum
from pathlib import Path
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.messages import BaseMessage
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.agents.cv_screening.cv_screener import evaluate_cv
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

class ToolCallRecord(BaseModel):
    """Records each tool invocation for debugging and replay"""
    timestamp: str
    tool_name: str
    stage: str
    input_args: Dict[str, Any]
    output: Optional[str] = None
    error: Optional[str] = None


class StageSummary(BaseModel):
    """Compacted output from a completed stage (context engineering)"""
    stage: str
    timestamp: str
    success: bool
    summary: str
    key_metrics: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class CandidateMemoryContext(BaseModel):
    """Candidate-specific state loaded for each task (stateless approach)"""
    candidate_id: str
    candidate_email: str
    cv_text: Optional[str] = None
    jd_text: Optional[str] = None
    stage_summaries: List[StageSummary] = Field(default_factory=list)
    tool_call_log: List[ToolCallRecord] = Field(default_factory=list)
    messages: List[Dict[str, Any]] = Field(default_factory=list)


class SubagentResult(BaseModel):
    """Standardized output from any subagent"""
    stage: str
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None


# ============================================================================
# 3. AGENT INVOCATION FUNCTIONS
# ============================================================================

def invoke_cv_screening_agent(
    cv_text: str,
    jd_text: str,
    candidate_id: str,
    tool_log: List[ToolCallRecord],
) -> SubagentResult:
    """
    Invoke CV Screening Agent (REAL implementation via evaluate_cv).
    """
    record = ToolCallRecord(
        timestamp=datetime.now().isoformat(),
        tool_name="cv_screening_agent",
        stage=WorkflowStage.CV_SCREENING.value,
        input_args={"candidate_id": candidate_id},
    )
    
    try:
        cv_output = evaluate_cv(cv_text, jd_text)
        record.output = f"CV score: {cv_output.overall_fit_score:.2f}"
        tool_log.append(record)
        
        return SubagentResult(
            stage=WorkflowStage.CV_SCREENING.value,
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
            stage=WorkflowStage.CV_SCREENING.value,
            success=False,
            data={},
            error=str(e),
        )


def invoke_voice_screening_agent(
    candidate_id: str,
    candidate_email: str,
    tool_log: List[ToolCallRecord],
) -> SubagentResult:
    """TODO: Voice Screening Agent - not yet implemented"""
    record = ToolCallRecord(
        timestamp=datetime.now().isoformat(),
        tool_name="voice_screening_agent",
        stage=WorkflowStage.VOICE_SCREENING.value,
        input_args={"candidate_id": candidate_id},
        error="TODO: Voice Screening Agent not yet implemented",
    )
    tool_log.append(record)
    
    return SubagentResult(
        stage=WorkflowStage.VOICE_SCREENING.value,
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
        stage=WorkflowStage.HR_SCHEDULING.value,
        input_args={"candidate_id": candidate_id},
        error="TODO: HR Scheduling Agent not yet implemented",
    )
    tool_log.append(record)
    
    return SubagentResult(
        stage=WorkflowStage.HR_SCHEDULING.value,
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
        stage=WorkflowStage.DECISION.value,
        input_args={"candidate_id": candidate_id},
        error="TODO: Decision Agent not yet implemented",
    )
    tool_log.append(record)
    
    return SubagentResult(
        stage=WorkflowStage.DECISION.value,
        success=False,
        data={},
        error="TODO: Decision Agent not yet implemented",
    )


# ============================================================================
# 4. CONTEXT ENGINEERING - REFLECTION & SUMMARY GENERATION
# ============================================================================

def generate_stage_summary(result: SubagentResult, agent_output: str = "") -> StageSummary:
    """
    Generate lightweight reflection summary after subagent execution.
    This compacts the output to prevent context pollution.
    """
    if result.stage == WorkflowStage.CV_SCREENING.value:
        return StageSummary(
            stage=result.stage,
            timestamp=datetime.now().isoformat(),
            success=result.success,
            summary=f"CV score: {result.data.get('overall_fit_score', 'N/A')} - {str(result.data.get('llm_feedback', 'N/A'))[:100]}...",
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
        summary=f"Stage {result.stage}: {'Success' if result.success else 'Failed'}",
        key_metrics=result.data,
    )


# ============================================================================
# 5. SUPERVISOR AGENT - MAIN ORCHESTRATOR (LLM-DRIVEN)
# ============================================================================

class HRSupervisor:
    """
    Supervisor Agent that orchestrates the HR recruitment workflow using LLM-driven
    AUTONOMOUS decision-making.
    
    All decisions are made by the LLM supervisor reasoning about candidate context,
    not by hardcoded rules. The supervisor:
    - Has access to tools for invoking agents
    - Uses its own reasoning to decide which agent to invoke
    - Processes tool results and autonomously determines next steps
    - Decides when to retry, skip stages, or complete the workflow
    
    Implements context engineering to prevent token bloat and improve reliability:
    1. Stateless subagent handling with context injection
    2. Reflection/summary generation after each step
    3. Candidate-specific state files
    4. Tool call logging and tracing
    5. Dashboard trace generation
    """
    
    def __init__(self):
        self.model = ChatOpenAI(model="gpt-4o", temperature=0.7)
        self.temp_dir = Path(tempfile.gettempdir())
        self.tools = self._create_agent_tools()
        self._current_memory: Optional[CandidateMemoryContext] = None
        # TODO: Load persistent memory summaries from database (supervisor.md Section 5)
    
    # ========================================================================
    # 1. TOOL DEFINITIONS - Tools the LLM supervisor can invoke
    # ========================================================================
    
    def _create_agent_tools(self) -> List:
        """Create tools that the supervisor LLM can autonomously invoke"""
        
        @tool
        def run_cv_screening(candidate_id: str, cv_text: str, jd_text: str) -> str:
            """
            Run CV Screening Agent to evaluate candidate's CV against job description.
            The agent analyzes skills match, experience, education alignment and overall fit.
            Returns a detailed scoring report.
            """
            if self._current_memory is None:
                return "ERROR: Memory context not initialized"
            
            result = invoke_cv_screening_agent(
                cv_text,
                jd_text,
                candidate_id,
                self._current_memory.tool_call_log,
            )
            
            # Reflect and summarize
            summary = generate_stage_summary(result)
            self._current_memory.stage_summaries.append(summary)
            
            if result.success:
                output = (
                    f"✓ CV Screening Complete\n"
                    f"  Overall Fit Score: {result.data.get('overall_fit_score', 'N/A')}\n"
                    f"  Skills Match: {result.data.get('skills_match_score', 'N/A')}\n"
                    f"  Experience Match: {result.data.get('experience_match_score', 'N/A')}\n"
                    f"  Education Match: {result.data.get('education_match_score', 'N/A')}\n"
                    f"  Feedback: {result.data.get('llm_feedback', 'N/A')}"
                )
            else:
                output = f"✗ CV Screening Failed: {result.error}"
            
            return output
        
        @tool
        def run_voice_screening(candidate_id: str, candidate_email: str) -> str:
            """
            Run Voice Screening Agent to conduct phone interview evaluation.
            TODO: Not yet implemented. Will evaluate communication skills and cultural fit.
            """
            if self._current_memory is None:
                return "ERROR: Memory context not initialized"
            
            result = invoke_voice_screening_agent(
                candidate_id,
                candidate_email,
                self._current_memory.tool_call_log,
            )
            
            summary = generate_stage_summary(result)
            self._current_memory.stage_summaries.append(summary)
            
            return f"⚠️ TODO: Voice Screening Agent is not yet implemented. This agent is unavailable. Continue the workflow without this step based on available information."
        
        @tool
        def run_hr_scheduling(candidate_id: str, candidate_email: str) -> str:
            """
            Run HR Scheduling Agent to schedule final interview with HR team.
            TODO: Not yet implemented. Will coordinate calendar availability.
            """
            if self._current_memory is None:
                return "ERROR: Memory context not initialized"
            
            result = invoke_scheduler_agent(
                candidate_id,
                candidate_email,
                self._current_memory.tool_call_log,
            )
            
            summary = generate_stage_summary(result)
            self._current_memory.stage_summaries.append(summary)
            
            return f"⚠️ TODO: HR Scheduling Agent is not yet implemented. This agent is unavailable. Continue the workflow without this step based on available information."
        
        @tool
        def run_decision_agent(candidate_id: str) -> str:
            """
            Run Decision Agent to make final hiring decision based on all previous evaluations.
            TODO: Not yet implemented. Will aggregate all stage results into hiring recommendation.
            """
            if self._current_memory is None:
                return "ERROR: Memory context not initialized"
            
            result = invoke_decision_agent(
                candidate_id,
                self._current_memory,
                self._current_memory.tool_call_log,
            )
            
            summary = generate_stage_summary(result)
            self._current_memory.stage_summaries.append(summary)
            
            return f"⚠️ TODO: Decision Agent is not yet implemented. This agent is unavailable. Make your own hiring decision based on all gathered information, or continue the workflow as you see fit."
        
        @tool
        def complete_workflow(candidate_id: str, decision: str) -> str:
            """
            Complete the workflow and finalize the hiring decision.
            
            Args:
                candidate_id: The candidate's ID
                decision: Final decision (e.g., "HIRE", "REJECT", "HOLD_FOR_REVIEW")
            
            Returns:
                Confirmation message
            """
            return f"Workflow completed for {candidate_id} with decision: {decision}"
        
        return [
            run_cv_screening,
            run_voice_screening,
            run_hr_scheduling,
            run_decision_agent,
            complete_workflow,
        ]
    
    # ========================================================================
    # 2. CANDIDATE STATE PERSISTENCE
    # ========================================================================
    
    def save_candidate_state(self, memory: CandidateMemoryContext) -> Path:
        """Save candidate-specific state to temporary file"""
        state_file = self.temp_dir / f"candidate_{memory.candidate_id}_state.json"
        state_file.write_text(json.dumps(json.loads(memory.model_dump_json()), indent=2))
        return state_file
    
    def cleanup_candidate_state(self, candidate_id: str) -> None:
        """Delete candidate state file when hiring decision is made"""
        # TODO: Implement multi-applicant context switching (supervisor.md Section 5)
        # Load/unload context from applicant-specific memory when handling concurrent candidates
        state_file = self.temp_dir / f"candidate_{candidate_id}_state.json"
        if state_file.exists():
            state_file.unlink()
    
    # ========================================================================
    # 3. MAIN WORKFLOW EXECUTOR - LLM-DRIVEN AUTONOMOUS LOOP
    # ========================================================================
    
    def run_workflow(
        self,
        candidate_id: str,
        candidate_email: str,
        cv_text: str,
        jd_text: str,
    ) -> Dict[str, Any]:
        """
        Execute complete workflow for a candidate using LLM-driven AUTONOMOUS decision-making.
        
        The supervisor LLM autonomously decides:
        - Which agent to run first
        - Based on results, which agent to run next
        - Whether to retry failed stages
        - Whether to skip stages
        - When the workflow is complete
        
        NO HARDCODED LOGIC WHATSOEVER - all decisions are made by LLM reasoning.
        
        Args:
            candidate_id: Unique candidate ID
            candidate_email: Candidate email
            cv_text: Candidate's CV
            jd_text: Job description
        
        Returns:
            Dictionary with final results and traces
        """
        print(f"    [1/4] Initializing workflow for {candidate_id}...")
        
        # TODO: Load candidate context from database (supervisor.md Section 5)
        # Load past runs and memory summaries for this candidate if they exist
        
        # Initialize memory
        memory = CandidateMemoryContext(
            candidate_id=candidate_id,
            candidate_email=candidate_email,
            cv_text=cv_text,
            jd_text=jd_text,
        )
        
        # TODO: Initialize default plan (supervisor.md Section 2)
        # Build initial sequence: CV Screening → Voice Screening → HR Interview Scheduling → Decision
        # LLM can still deviate autonomously, but this provides a starting template
        
        # Store reference for tools to access
        self._current_memory = memory
        
        print(f"    ✓ Memory initialized")
        
        # Build initial system prompt for supervisor LLM
        # This is where ALL the decision logic lives now - in the LLM's reasoning
        system_prompt = f"""You are an autonomous HR Recruitment Supervisor Agent.

YOUR GOAL:
Conduct a thorough recruitment evaluation of candidate {candidate_id} and make a hiring decision
(HIRE, REJECT, or HOLD_FOR_REVIEW). You must evaluate the candidate fairly and comprehensively
using available information.

YOUR AUTONOMY:
You have COMPLETE autonomy over HOW you achieve this goal:
- Which agents to invoke and in what order
- Whether to retry agents that fail
- Whether to skip unavailable agents and compensate with available data
- How to interpret agent outputs
- When you have sufficient information to make a decision

You do NOT have autonomy over the GOAL itself - you must make a hiring decision.
There are NO hardcoded rules dictating your workflow - you decide everything.

AVAILABLE TOOLS:
1. run_cv_screening - Evaluates candidate's CV vs job description (✓ IMPLEMENTED)
2. run_voice_screening - TODO: Phone interview evaluation (⚠️ NOT AVAILABLE)
3. run_hr_scheduling - TODO: Schedule final interview (⚠️ NOT AVAILABLE)
4. run_decision_agent - TODO: Aggregates data into recommendation (⚠️ NOT AVAILABLE)
5. complete_workflow - End workflow with your hiring decision (✓ USE THIS TO FINISH)

CANDIDATE INFORMATION:
- ID: {candidate_id}
- Email: {candidate_email}
- CV and Job Description: Available through run_cv_screening tool

WORKFLOW APPROACH:
1. Start with run_cv_screening to evaluate the CV against job description
2. Interpret the CV screening results
3. If unavailable agents are needed, work around them or make decisions based on available data
4. When you have sufficient information, use complete_workflow with your decision

IMPORTANT NOTES:
- When tools return "TODO: Not yet implemented", this agent is genuinely unavailable
- Adapt your approach - you can make decisions based on CV data alone if needed
- Be thorough but efficient
- Make reasonable hiring decisions with the information you have
- Use complete_workflow to end the process with HIRE, REJECT, or HOLD_FOR_REVIEW

Begin the recruitment workflow for {candidate_id}. Use your autonomous judgment."""
        
        print(f"    [2/4] Starting LLM-driven workflow loop...")
        
        messages: List[BaseMessage] = [SystemMessage(content=system_prompt)]
        
        # Add initial human message to start the workflow
        messages.append(
            HumanMessage(
                content=f"Evaluate candidate {candidate_id} and make a hiring decision. "
                f"Use your available tools as needed, and make your own decisions about "
                f"workflow progression. End with complete_workflow and your final decision."
            )
        )
        
        # Agentic loop - LLM makes all decisions
        max_iterations = 15
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n    [Iteration {iteration}/{max_iterations}] Running supervisor LLM...")
            
            # Bind tools to model
            model_with_tools = self.model.bind_tools(self.tools)
            
            # Get response from LLM
            response = model_with_tools.invoke(messages)
            print(f"      ✓ LLM responded")
            
            # Add response to message history
            messages.append(response)
            memory.messages.append({"role": "assistant", "content": str(response)})
            
            # Check if LLM is done (no tool calls)
            if not hasattr(response, "tool_calls") or not response.tool_calls:
                print(f"      → LLM finished (no more tool calls)")
                break
            
            # Process each tool call (LLM's autonomous decisions)
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call["id"]
                
                print(f"      → LLM invoked tool: {tool_name}")
                
                # Find and execute the tool
                tool_result = None
                for tool in self.tools:
                    if tool.name == tool_name:
                        try:
                            tool_result = tool.invoke(tool_args)
                            print(f"        ✓ Tool executed")
                        except Exception as e:
                            tool_result = f"ERROR: {str(e)}"
                            print(f"        ✗ Tool error: {tool_result}")
                        break
                
                if tool_result is None:
                    tool_result = f"ERROR: Tool {tool_name} not found"
                
                # Add tool result to messages
                tool_message = ToolMessage(
                    content=tool_result,
                    tool_call_id=tool_id,
                    name=tool_name,
                )
                messages.append(tool_message)
                memory.messages.append(
                    {"role": "tool", "content": tool_result, "name": tool_name}
                )
                
                # Check if workflow is complete
                if tool_name == "complete_workflow":
                    print(f"      → LLM completed workflow")
                    iteration = max_iterations  # Break outer loop
                    break
        
        print(f"\n    [3/4] Generating final trace...")
        trace = self.get_reasoning_trace(memory)
        print(f"    ✓ Trace generated")
        
        print(f"    [4/4] Finalizing workflow...")
        # Save final state
        self.save_candidate_state(memory)
        
        # TODO: Delete candidate state file only when hiring decision is finalized (supervisor.md Section 5)
        # Conditionally cleanup based on whether a final decision (HIRE/REJECT) was made, not unconditionally
        # self.cleanup_candidate_state(candidate_id)
        print(f"    ✓ Workflow finalized")
        
        return trace
    
    # ========================================================================
    # 4. DASHBOARD TRACE GENERATION
    # ========================================================================
    
    def get_reasoning_trace(self, memory: CandidateMemoryContext) -> Dict[str, Any]:
        """
        Generate structured trace for dashboard visualization.
        Includes memory summaries, tool logs, and LLM reasoning.
        
        Args:
            memory: Candidate memory context
        
        Returns:
            Structured trace dictionary
        """
        return {
            "candidate_id": memory.candidate_id,
            "workflow_summary": {
                "total_stages_run": len(memory.stage_summaries),
                "successful_stages": sum(1 for s in memory.stage_summaries if s.success),
                "failed_stages": sum(1 for s in memory.stage_summaries if not s.success),
            },
            "stage_summaries": [s.model_dump() for s in memory.stage_summaries],
            "tool_calls": [tc.model_dump() for tc in memory.tool_call_log],
            "conversation_history": memory.messages,
        }