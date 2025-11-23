"""CV Screening Agent Module

Run as follows:
>>> docker compose up --build
>>> docker compose run --rm candidates_db_init python -m src.agents.cv_screening.screener
"""


import json
from langchain_openai import ChatOpenAI
from langchain.messages import SystemMessage, HumanMessage

from dotenv import load_dotenv
from src.agents.cv_screening.schemas.output_schema import CVScreeningOutput
from src.agents.cv_screening.utils import read_file, write_results_to_db

load_dotenv()




# --- The evaluator function ---
def screen_cv(cv_text: str, jd_text: str) -> CVScreeningOutput:
    """
    Evaluate a candidate's CV against a job description using an LLM.

    Args:
        cv_text (str): The text content of the candidate's CV.
        jd_text (str): The text content of the Job Description.

    Returns:
        CVScreeningOutput: The structured screening result.
        Makes model write feedback before scoring, leading to better calibration
        and genuine reasoning that leads to more balanced scores.

        **NOTE**: 
        >>> The model generates feedback first (Chain-of-Thought) 
        >>> to ensure calibrated scores.

    """
    llm = (
        ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=1500,
        )
        .with_structured_output(CVScreeningOutput)
    )

    messages = [
        # Instruction
        SystemMessage(
            content=(
                "You are an HR assistant evaluating how well a candidate's CV matches a given job description. "
                "Generate a concise assessment summary first to ground your reasoning. "
                "Then assign calibrated match scores between 0 and 1. "
                "The scores should be based on the following criteria: "
                "   1. Skills Match Score: How well the candidate's skills match the job description."
                "   2. Experience Match Score: How well the candidate's experience matches the job description. "
                "   3. Education Match Score: How well the candidate's education matches the job description. "
                "   4. Overall Fit Score: How well the candidate's CV fits the job description. "
            )
        ),
        # Payload
        HumanMessage(
            content=(
                f"Job Description:\n{jd_text}\n\n"
                f"Candidate CV:\n{cv_text}\n"
            )
        ),
    ]

    return llm.invoke(messages)



# --- Main execution for testing ---
if __name__ == "__main__":
    from pathlib import Path
    #BASE_PATH = Path("/Users/sebastianwefers/Desktop/projects/recruitment-agent/src/database")
    BASE_PATH = Path(__file__).resolve().parents[2] / "database"

    cv_text = read_file(BASE_PATH / "cvs/parsed/c762271c-af8f-49db-acbb-e37e5f0f0f98_SWefers_CV-sections.txt")
    jd_text = read_file(BASE_PATH / "cvs/job_postings/ai_engineer.txt")

    # trigger evaluation
    result = screen_cv(cv_text, jd_text)
    print(json.dumps(result.model_dump(), indent=2))

    # optionally write to DB
    write_results_to_db(
        candidate_email="sebastianwefersnz@gmail.com",
        result=result,
        job_title="AI Engineer"
    )