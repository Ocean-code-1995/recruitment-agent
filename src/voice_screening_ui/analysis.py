"""
Simple analysis function for voice screening transcripts.
No LangGraph - just a direct OpenAI API call.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.voice_screening.schemas.output_schema import VoiceScreeningOutput


def analyze_transcript(transcript_text: str) -> VoiceScreeningOutput:
    """
    Analyze a voice screening transcript using OpenAI GPT-4.
    
    Args:
        transcript_text: Full conversation transcript as text
        
    Returns:
        VoiceScreeningOutput: Structured analysis results
    """
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.0,
    ).with_structured_output(VoiceScreeningOutput)
    
    system_prompt = """You are an HR assistant analyzing a voice screening interview transcript.
    Evaluate the candidate's responses for:
    1. Sentiment (overall positive/negative tone) - score 0-1
    2. Confidence (how confidently they answered) - score 0-1
    3. Communication (clarity, articulation, professionalism) - score 0-1
    
    Provide scores between 0 and 1 for each metric, a comprehensive summary, 
    identify key traits, and provide a recommendation (pass/fail/next steps)."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Interview Transcript:\n\n{transcript_text}")
    ]
    
    result = llm.invoke(messages)
    return result

