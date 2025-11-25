import sys
import os

# Add project root to path to ensure we can import from src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(project_root)

from src.prompts import get_prompt

def test_fetch_prompt():
    prompt_name = "DB_Executor"
    print(f"Attempting to fetch prompt: {prompt_name}")
    
    try:
        # Using latest_version=True to test the new feature and bypass env labels
        print(f"Fetching prompt '{prompt_name}' using latest_version=True...")
        prompt = get_prompt(prompt_name, latest_version=True)
        print(f"\n✅ Successfully fetched '{prompt_name}':")
        print("-" * 40)
        print(prompt)
        print("-" * 40)
    except Exception as e:
        print(f"\n❌ Error fetching prompt: {e}")

if __name__ == "__main__":
    test_fetch_prompt()
