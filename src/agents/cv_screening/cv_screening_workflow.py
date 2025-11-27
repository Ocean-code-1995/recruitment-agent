from pathlib import Path
from langchain_core.tools import tool


from src.agents.cv_screening.cv_screener import screen_cv
from src.agents.cv_screening.utils import read_file
from src.database.candidates import (
    write_cv_results_to_db,
    get_candidate_by_name,
)

@tool
def cv_screening_workflow(candidate_full_name: str = "") -> str:
    """
    Runs the deterministic CV screening workflow for a candidate.
    This is a fixed sequential process, not a reasoning agent.

    Steps:
    1. Retrieve candidate info from DB
    2. Read files (CV & Job Description)
    3. Evaluate CV
    4. Store results in DB & update status

    Args:
        candidate_full_name (str): The full name of the candidate to screen.

    Returns:
        str: A message indicating the outcome of the workflow. (✅ or ❌)
    """
    if not candidate_full_name:
        return "❌ Candidate name is required."

    # 1️⃣ Retrieve candidate info from DB
    print(f"🔍 Looking up candidate: {candidate_full_name}")
    candidate = get_candidate_by_name(candidate_full_name)
    
    if not candidate:
        return f"❌ Candidate '{candidate_full_name}' not found in database."

    candidate_email = candidate["email"]
    cv_path_str = candidate["parsed_cv_file_path"]
    
    if not cv_path_str:
        return f"❌ No parsed CV path recorded for '{candidate_full_name}'."

    # Resolve paths
    # Assuming the parsed path in DB is relative to project root (e.g., src/database/cvs/parsed/...)
    # We need to ensure we can find it.
    
    # Calculate project root from this file location
    # src/agents/cv_screening/cv_screening_workflow.py -> 3 levels up to src -> 4 to root
    root_dir = Path(__file__).resolve().parents[3]
    
    cv_path = root_dir / cv_path_str
    if not cv_path.exists():
        # Try treating it as absolute or check if the path in DB was absolute
        cv_path = Path(cv_path_str)
        if not cv_path.exists():
            return f"❌ CV file not found at: {cv_path}"

    # JD path is constant for this MVP
    jd_path = root_dir / "src/database/job_postings/ai_engineer.txt"
    
    if not jd_path.exists():
        return f"❌ Job description not found at: {jd_path}"

    # 2️⃣ Read files
    print(f"📄 Reading Job Description from: {jd_path}")
    jd_text = read_file(jd_path)
    
    print(f"📄 Reading CV from: {cv_path}")
    cv_text = read_file(cv_path)
    

    # 3️⃣ Evaluate CV
    print("🧠 Running LLM screening...")
    try:
        result = screen_cv(cv_text, jd_text)
    except Exception as e:
        return f"❌ Error during LLM screening: {str(e)}"

    # 4️⃣ Store results in DB & update status
    print("💾 Saving results to database...")
    try:
        write_cv_results_to_db(
            candidate_email=candidate_email,
            result=result,
            job_title="AI Engineer"
        )
    except Exception as e:
        return f"❌ Error saving results to DB: {str(e)}"
    
    return f"✅ CV Screening Workflow completed successfully for {candidate_full_name}. Scores and feedback have been saved to the database."




if __name__ == "__main__":
    # Example usage for testing
    # You can run this directly if you have a candidate in the DB
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else "Ada Lovelace"
    cv_screening_workflow(name)
