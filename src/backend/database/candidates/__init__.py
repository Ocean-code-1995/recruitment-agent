"""
Candidates database module.

All database operations are organized in the ops/ folder, 
with each operation in its own file for modularity.
"""

from .ops import (
    register_candidate,
    update_parsed_cv_path,
    get_candidate_by_name,
    update_application_status,
    write_cv_results_to_db,
    write_voice_results_to_db,
    evaluate_cv_screening_decision,
)

__all__ = [
    "register_candidate",
    "update_parsed_cv_path",
    "get_candidate_by_name",
    "update_application_status",
    "write_cv_results_to_db",
    "write_voice_results_to_db",
    "evaluate_cv_screening_decision",
]
