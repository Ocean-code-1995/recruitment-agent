import json
from datetime import datetime
from typing import Optional
from uuid import UUID

from langchain_openai import ChatOpenAI
from langchain.messages import SystemMessage, HumanMessage
from sqlalchemy import select

from src.database.candidates.client import SessionLocal
from src.database.candidates.models import Candidate, VoiceScreeningResult, CVScreeningResult
from src.state.candidate import CandidateStatus
from src.agents.voice_screening.schemas.output_schema import VoiceScreeningOutput
from src.prompts import get_prompt

import base64
import os

# Initialize LLM
# We will instantiate the model dynamically based on input availability

SYSTEM_PROMPT = get_prompt(
    template_name="Voice_Screening_Judge",
    latest_version=True
)


def evaluate_voice_screening(candidate_id: str) -> str:
    """
    Evaluates a completed voice screening session for a candidate.
    
    Args:
        candidate_id (str): The UUID of the candidate to evaluate.
        
    Returns:
        str: A summary of the evaluation result.
    """
    try:
        with SessionLocal() as session:
            # 1. Fetch Candidate and VoiceScreeningResult
            candidate = session.execute(
                select(Candidate).where(Candidate.id == UUID(candidate_id))
            ).scalar_one_or_none()
            
            if not candidate:
                return f"❌ Candidate {candidate_id} not found."
            
            # Fetch latest voice screening result
            voice_result = session.execute(
                select(VoiceScreeningResult)
                .where(VoiceScreeningResult.candidate_id == UUID(candidate_id))
                .order_by(VoiceScreeningResult.timestamp.desc())
            ).scalar_one_or_none()
            
            if not voice_result or not voice_result.transcript_text:
                return f"❌ No voice screening transcript found for candidate {candidate.full_name}."
            
            # Fetch job title from CV screening result (for context)
            cv_result = session.execute(
                select(CVScreeningResult)
                .where(CVScreeningResult.candidate_id == UUID(candidate_id))
                .order_by(CVScreeningResult.timestamp.desc())
            ).scalar_one_or_none()
            
            job_title = cv_result.job_title if cv_result else "the position"
            
            # 2. Prepare Input (Audio + Text)
            messages = []
            
            messages.append(SystemMessage(content=SYSTEM_PROMPT))
            
            user_content = []
            user_content.append({"type": "text", "text": f"Candidate: {candidate.full_name}\nPosition: {job_title}\n"})
            
            # Try to load audio
            audio_loaded = False
            if voice_result.audio_url and os.path.exists(voice_result.audio_url):
                try:
                    with open(voice_result.audio_url, "rb") as audio_file:
                        audio_data = base64.b64encode(audio_file.read()).decode("utf-8")
                        user_content.append({
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_data,
                                "format": "wav"
                            }
                        })
                        audio_loaded = True
                except Exception as e:
                    print(f"⚠️ Failed to load audio file: {e}")
            
            # Always include transcript as text context
            user_content.append({"type": "text", "text": f"Transcript:\n{voice_result.transcript_text}\n"})
            
            messages.append(HumanMessage(content=user_content))
            
            # 3. Call LLM
            # Use audio-capable model if audio is loaded, otherwise standard model
            model_name = "gpt-4o-audio-preview" if audio_loaded else "gpt-4o"
            llm = ChatOpenAI(model=model_name, temperature=0)
            
            # gpt-4o-audio-preview doesn't support 'json_schema' response format yet, use function calling
            method = "function_calling" if audio_loaded else "function_calling" 
            
            structured_llm = llm.with_structured_output(VoiceScreeningOutput, method=method)
            evaluation: VoiceScreeningOutput = structured_llm.invoke(messages)
            
            # 4. Update Database
            voice_result.sentiment_score = evaluation.sentiment_score
            voice_result.confidence_score = evaluation.confidence_score
            voice_result.communication_score = evaluation.communication_score
            voice_result.proficiency_score = evaluation.proficiency_score
            voice_result.llm_summary = evaluation.llm_summary
            # voice_result.llm_judgment_json = evaluation.model_dump() # Removed from schema
            
            # 5. Determine Pass/Fail
            # Calculate average score (0-1 scale -> 0-100 scale for threshold comparison)
            avg_score = (
                evaluation.sentiment_score + 
                evaluation.confidence_score + 
                evaluation.communication_score + 
                evaluation.proficiency_score
            ) / 4.0 * 100
            
            if avg_score >= 75:
                candidate.status = CandidateStatus.voice_passed
                result_msg = "PASSED"
            else:
                candidate.status = CandidateStatus.voice_rejected
                result_msg = "REJECTED"
                
            candidate.updated_at = datetime.utcnow()
            session.commit()
            
            return (
                f"✅ Evaluation complete for {candidate.full_name} using {model_name}.\n"
                f"Result: {result_msg} (Score: {avg_score:.1f}/100)\n"
                f"Summary: {evaluation.llm_summary}"
            )
            
    except Exception as e:
        import traceback
        return f"❌ Error evaluating voice screening: {str(e)}\n{traceback.format_exc()}"