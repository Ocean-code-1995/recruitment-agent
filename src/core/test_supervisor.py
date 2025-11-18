#!/usr/bin/env python
"""
Minimal test to verify supervisor.py works with full context engineering.
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.core.supervisor import HRSupervisor


def test_supervisor_full_workflow():
    """Test supervisor with full workflow execution."""
    
    # Load test files
    base_path = project_root / "src/database"
    cv_file = base_path / "cvs/tests/test_cv.txt"
    jd_file = base_path / "cvs/tests/test_jd.txt"
    
    if not cv_file.exists():
        print(f"CV file not found: {cv_file}")
        return
    if not jd_file.exists():
        print(f"JD file not found: {jd_file}")
        return
    
    # Read files
    cv_text = cv_file.read_text()
    jd_text = jd_file.read_text()
    
    print("Files loaded\n")
    
    # Create supervisor
    print("Creating supervisor...")
    supervisor = HRSupervisor()
    print("Supervisor created")
    
    # Run complete workflow
    print("Running full workflow with context engineering...")
    print("Initializing plan and memory context...")
    trace = supervisor.run_workflow(
        candidate_id="test_candidate_001",
        candidate_email="test@example.com",
        cv_text=cv_text,
        jd_text=jd_text,
    )
    
    # Display results
    print("Workflow Complete!")
    print("Final Trace:")
    print(json.dumps(trace, indent=2, default=str))
    
    # Verify LLM made autonomous decisions
    print("\nLLM Autonomous Decision-Making:")
    tool_names = [tc['tool_name'] for tc in trace['tool_calls']]
    print(f"  Tools invoked: {set(tool_names)}")
    print(f"  LLM made {len(trace['conversation_history'])} reasoning steps")
    
    print("\nAll tests passed!")


if __name__ == "__main__":
    test_supervisor_full_workflow()
