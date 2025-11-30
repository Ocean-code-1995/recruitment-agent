# Video Demo Script

This script outlines the flow and queries for the demo video.

## Prerequisites / Setup


Manually create:
1. **Existing Candidate**: "Jane Doe"
   - Status: `voice_passed` (Ready for final interview)
   - Includes fake CV and Voice Screening results for the agent to analyze.


## Demo Flow

### 1. The New Applicant & Morning Check-in
*Action 1: Switch to the **CV Portal UI** and upload a new CV for "Alex Smith" (applying him to the system).*

*Goal: Show the agent's awareness of the current database state (both old and new candidates).*

**Query 1:**
```text
Hi! Can you give me a summary of the current recruitment status? Who are the active candidates and what stages are they in?
```


---

### 2. CV Screening
*Goal: Demonstrate the CV screening workflow.*

**Query 2:**
```text
I see PERSON X is a new applicant. Can you please screen his CV and summarize the feedback and his score?
```

**Query 3:**
```text
Send him an email invitation for the voice screening!
```

-> Then do voice screening!

---

### 3. Reviewing the Candidate
*Goal: Show the "Voice Judge" results and Calendar/Email integration.*

**Query 4:**
```text
I see she/he completed the voice screening. Can you analyze her interview transcript and tell me how she performed?
```

*(Expected Response: Agent reads the voice analysis/judge score and summarizes the candidate's strengths/weaknesses.)*

**Query 5:**
```text
That sounds promising. Let's move her to the final stage. Please schedule a person-to-person interview with her for next Tuesday at 10 AM. Add it to the HR calendar and send her a calendar invitation.
```

---

### 4. Final Status Check
*Goal: Confirm all actions were executed.*

**Query 6:**
```text
Thanks! Can you show me the updated pipeline status?
```
