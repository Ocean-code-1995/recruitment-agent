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
        cv_text (str): The candidate's CV text.
        jd_text (str): The job description text.

    Returns:
        CVScreeningResult: The structured screening result.
        Makes model write feedback before scoring, leading to better calibration
        and genuine reasoning that leads to more balanced scores.
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
        SystemMessage(
            content=(
                "You are an HR assistant evaluating how well a candidate's CV matches a given job description. "
                "First, provide a short textual summary of your assessment. "
                "Then, provide structured numeric scores between 0 and 1, and a short textual summary."
            )
        ),
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