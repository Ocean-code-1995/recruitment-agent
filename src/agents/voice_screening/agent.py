"""
Voice Screening Agent - LangGraph-based agent for conducting voice interviews.
"""
from typing import TypedDict, Annotated, List, Optional, Dict, Any
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.core.base_agent import BaseAgent
from src.core.configs.agent import AgentConfig
from src.agents.voice_screening.schemas.output_schema import (
    VoiceScreeningOutput,
    ConversationState,
    CallTranscript
)
from src.agents.voice_screening.utils.db import write_voice_results_to_db
from src.agents.voice_screening.utils.twilio_client import initiate_outbound_call
import os


class VoiceScreeningState(TypedDict):
    """State for voice screening agent."""
    candidate_id: str
    phone_number: str
    call_sid: Optional[str]
    transcript: List[CallTranscript]
    conversation_state: Optional[ConversationState]
    interview_questions: List[str]
    current_question_index: int
    call_active: bool
    analysis_result: Optional[VoiceScreeningOutput]
    messages: Annotated[List[Any], "messages"]


class VoiceScreeningAgent(BaseAgent):
    """LangGraph agent for conducting voice screening interviews."""
    
    def __init__(self, config: AgentConfig):
        """Initialize the voice screening agent."""
        super().__init__(config)
        self.webhook_base_url = os.getenv("VOICE_SCREENING_WEBHOOK_URL", "")
        self.twilio_phone = os.getenv("TWILIO_PHONE_NUMBER", "")
        
    def build_graph(self) -> StateGraph:
        """Build the LangGraph structure for voice screening."""
        workflow = StateGraph(VoiceScreeningState)
        
        # Add nodes
        workflow.add_node("initiate_call", self._initiate_call_node)
        workflow.add_node("handle_conversation", self._handle_conversation_node)
        workflow.add_node("analyze_call", self._analyze_call_node)
        workflow.add_node("update_database", self._update_database_node)
        
        # Define flow
        workflow.add_edge(START, "initiate_call")
        workflow.add_edge("initiate_call", END)  # Call runs asynchronously, FastAPI handles it
        workflow.add_edge("analyze_call", "update_database")
        workflow.add_edge("update_database", END)
        
        return workflow
    
    def _initiate_call_node(self, state: VoiceScreeningState) -> VoiceScreeningState:
        """Initiate an outbound call via Twilio."""
        webhook_url = f"{self.webhook_base_url}/voice/webhook"
        media_url = f"{self.webhook_base_url}/voice/media"
        
        call_sid = initiate_outbound_call(
            to_phone=state["phone_number"],
            from_phone=self.twilio_phone,
            webhook_url=webhook_url,
            media_stream_url=media_url
        )
        
        return {
            **state,
            "call_sid": call_sid,
            "call_active": True,
            "transcript": [],
            "current_question_index": 0
        }
    
    def _handle_conversation_node(self, state: VoiceScreeningState) -> VoiceScreeningState:
        """
        Handle conversation logic during the call.
        This is called by FastAPI during the call for each turn.
        """
        # Generate interview questions if not already set
        if not state.get("interview_questions"):
            questions = self._generate_interview_questions(state.get("candidate_id", ""))
            state["interview_questions"] = questions
        
        # Get current question
        current_idx = state.get("current_question_index", 0)
        questions = state.get("interview_questions", [])
        
        if current_idx < len(questions):
            next_question = questions[current_idx]
        else:
            # End of interview
            next_question = "Thank you for your time. We'll be in touch soon."
        
        # Update state
        return {
            **state,
            "current_question_index": current_idx + 1
        }
    
    def _generate_interview_questions(self, candidate_id: str) -> List[str]:
        """Generate interview questions based on candidate and job."""
        # For now, return standard questions
        # In production, this could query the database for candidate info and job description
        return [
            "Tell me about yourself and your background.",
            "What interests you about this position?",
            "Can you describe a challenging project you've worked on?",
            "What are your strengths and areas for growth?",
            "Do you have any questions for us?"
        ]
    
    def _analyze_call_node(self, state: VoiceScreeningState) -> VoiceScreeningState:
        """
        Analyze the call transcript using LLM.
        This is called after the call ends.
        """
        # Build transcript text
        transcript_text = "\n".join([
            f"{t.speaker}: {t.text}" for t in state.get("transcript", [])
        ])
        
        # Use LLM to analyze
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.0,
        ).with_structured_output(VoiceScreeningOutput)
        
        system_prompt = """You are an HR assistant analyzing a voice screening interview transcript.
        Evaluate the candidate's responses for:
        1. Sentiment (overall positive/negative tone)
        2. Confidence (how confidently they answered)
        3. Communication (clarity, articulation, professionalism)
        
        Provide scores between 0 and 1 for each metric, a summary, and a recommendation."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Interview Transcript:\n\n{transcript_text}")
        ]
        
        result = llm.invoke(messages)
        
        return {
            **state,
            "analysis_result": result
        }
    
    def _update_database_node(self, state: VoiceScreeningState) -> VoiceScreeningState:
        """Save results to database."""
        transcript_text = "\n".join([
            f"{t.speaker}: {t.text}" for t in state.get("transcript", [])
        ])
        
        analysis_result = state.get("analysis_result")
        if not analysis_result:
            raise ValueError("Analysis result must be present before updating database")
        
        write_voice_results_to_db(
            candidate_id=state["candidate_id"],
            call_sid=state.get("call_sid", ""),
            transcript_text=transcript_text,
            result=analysis_result
        )
        
        return state
    
    def start_voice_screening(self, candidate_id: str, phone_number: str) -> str:
        """
        Public method to start a voice screening call.
        This is the tool that the supervisor agent will call.
        
        Args:
            candidate_id: UUID of the candidate
            phone_number: Phone number in E.164 format
            
        Returns:
            str: Twilio Call SID
        """
        initial_state: VoiceScreeningState = {
            "candidate_id": candidate_id,
            "phone_number": phone_number,
            "call_sid": None,
            "transcript": [],
            "conversation_state": None,
            "interview_questions": [],
            "current_question_index": 0,
            "call_active": False,
            "analysis_result": None,
            "messages": []
        }
        
        result = self.invoke(initial_state)
        return result.get("call_sid", "")

