
from .cv_screener import screen_cv
from src.agents.cv_screening.utils import read_file, write_results_to_db



def cv_screening_workflow(cv_text: str, jd_text: str = "", candidate_email: str = "") :
    

    # read job description & cv text
    jd_text = read_file(jd_path)
    cv_text = read_file(cv_path)
    

    # evaluate cv
    result = screen_cv(cv_text, jd_text)

    # store results in db if email provided
