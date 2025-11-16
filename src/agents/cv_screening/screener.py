import json
from openai import OpenAI
from dotenv import load_dotenv
from src.database.candidates.models import  CVScreeningResult
from src.agents.cv_screening.schemas.output_schema import CVScreeningOutput
from src.agents.cv_screening.utils.read_file import read_file
from src.agents.cv_screening.utils.db import write_results_to_db

load_dotenv()
client = OpenAI()


# --- The evaluator function ---
def evaluate_cv(cv_text: str, jd_text: str) -> CVScreeningResult:
    response = client.responses.parse(
        model="gpt-4o-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "You are an HR assistant evaluating how well a candidate's CV "
                    "matches a given job description. "
                    "Provide structured numeric scores between 0 and 1, "
                    "and a short textual summary."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Job Description:\n{jd_text}\n\n"
                    f"Candidate CV:\n{cv_text}\n"
                ),
            },
        ],
        text_format=CVScreeningOutput,
    )

    return response.output_parsed



# --- Main execution for testing ---
if __name__ == "__main__":
    from pathlib import Path
    BASE_PATH = Path("/Users/sebastianwefers/Desktop/projects/recruitment-agent/src/database")

    cv_text = read_file(BASE_PATH / "cvs/parsed/c762271c-af8f-49db-acbb-e37e5f0f0f98_SWefers_CV-sections.txt")
    jd_text = read_file(BASE_PATH / "cvs/job_postings/ai_engineer.txt")

    # trigger evaluation
    result = evaluate_cv(cv_text, jd_text)
    print(json.dumps(result.model_dump(), indent=2))

    # optionally write to DB
    write_results_to_db(
        candidate_email="sebastianwefersnz@gmail.com",
        result=result,
        job_title="AI Engineer"
    )

    # when willing to write results to db, do `compose up" and then:
    # >>> POSTGRES_HOST=localhost python -m src.agents.cv_screening.screener
