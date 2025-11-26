# Queries
These queries / tests are used to test how well the supervisor agent performs by evaluating its responses to various tasks.

## 1. Run CV screening for a newly uploaded candidate
### Queries
- "Please screen the new applicant and update their status accordingly."
- "Please check if there is any applicants. Please tell me who if so. Then send them to the cv screening and update their status accordingly"

### Expected behavior
Supervisor identifies that the candidate is in a state requiring CV screening.  
Supervisor delegates the work to the CV Screening agent.  
CV Screening agent parses the CV, scores it, determines pass or fail, and writes results into the database via the DB Executor.  
Supervisor waits for the tool output and then reports the updated status without performing the screening itself.
### Notes / issues
- The supervisor asks for the name of the applicant. Instead it should have automatically delegated it to the DB Executor. It needs to be less reliant on the user for something this trivial.
- The DB agent keeps trying to get a file at src\database\cvs\parsed\1dd5c1f2-737e-430f-9747-8b77d60219f3_SWefers_CV.txt. That path doesn't exist. Something is confusing it on which path the CVs are at.

***`Comments`: Note that the cv screening workflow currently only set status to **applied**. Status quo is to let db executor run the eval. Was not sure yesterday to already include **devision node** in cv screening workflow. But would defintiely make it more autonomous. For now I decided to attach `cv screening decision tool`to db agent, where the supervisor can set a threshold of what defines fail vs. pass***

---

## 2. Process multiple new candidates simultaneously
### Query

**Queries:**
- "We have several new applicants. Process all of them and let me know how the screening went."

- """We have two applicants in our database: one has just applied and the other has passed CV screening, correct? 
Please confirm that first and tell me what the actual statuses are.

Then:
- If one has status "applied", send him to the voice screening.
- If the other candidate has successfully passed the CV screening, then prepare a congratulatory email. 
    - Before preparing the email, check our calendar for available time slots for a person-to-person interview.
    - Include these available time slots in the email.

At the end, summarize the actions you took.
"""
### Expected behavior
Supervisor queries current candidate states via DB Executor and identifies all candidates in the new or cv_uploaded state.  
Supervisor routes each candidate to the CV Screening agent using isolated per candidate threads.  
Each CV Screening agent run updates the database through DB Executor.  
Supervisor receives aggregated outcomes and summarizes them for HR.
### Notes / issues
TODO

---

## 3. Notify a passed candidate and request time slots
### Query
"This candidate X passed screening. Notify them and ask for their availability."
### Expected behavior
Supervisor detects that the candidate is in a screened_passed state.  
Supervisor delegates email sending to the Gmail Agent.  
Gmail Agent contacts Gmail MCP to send the message.  
DB Executor updates the candidate status to awaiting_time_slots.  
Supervisor reports the next expected step.
### Notes / issues
- Works correctly. Asked DB Executor for email, then sent the email.

---

## 4. Notify a failed candidate
### Query
"The screening result is fail. Please notify the candidate and update the system."
### Expected behavior
Supervisor sees the screened_failed state.  
Supervisor calls the Gmail Agent.  
Gmail Agent sends a rejection email using Gmail MCP.  
DB Executor updates status to rejected.  
Supervisor returns a clean confirmation.
### Notes / issues
- Gmail has issue without using `--allow-blocking` when launching `langgraph dev`. But this also breaks the database.
- Gmail agent kept asking multiple times whether info was correct, even after being told yes. It needs
to just do what it is told.

***`Comment:`*** sending emails works for me on mac without any issues. not sure whether windows thing?

---

## 5. Generate a system wide status report
### Query
"What is the current status of all candidates?"
### Expected behavior
Supervisor calls DB Executor to retrieve aggregated counts and per status numbers.  
Supervisor formats the report for HR.  
No state transitions occur.  
No subagent beyond DB Executor is involved.
### Notes / issues
- Worked correctly without issues.

---

## 6. Schedule an interview for a candidate with provided availability
### Query
"The candidate already provided availability. Please schedule their interview."
### Expected behavior
Supervisor determines the candidate is in awaiting_time_slots and that availability is present in the DB.  
Supervisor calls the Calendar Agent.  
Calendar Agent uses the Calendar MCP to match candidate availability with HR calendar and schedules a meeting.  
DB Executor updates the status to interview_scheduled.  
Supervisor reports the scheduled event.
### Notes / issues
- Works correctly. Asked DB Executor for email, then sent the email.

---

## 7. Process all candidates to their next required step
### Query
"Process all candidates and advance everyone to the next appropriate step."
### Expected behavior
Supervisor retrieves all candidates via DB Executor.  
Supervisor groups them by workflow state and delegates each group to the appropriate subagent (CV Screening, Gmail Agent, Calendar Agent).  
All work is executed per candidate thread.  
DB Executor performs all writes.  
Supervisor produces a summary of completed actions.
### Notes / issues
- Got lots of database errors and missing CVs (the CVs should be in the DB, they're in the files). The DB Executor needs to have clearer instructions for how to use it, and be more persistant. It cannot give up if it fails once.

***`Comment`: we are still at single candidate mvp.*** `BUT`we should still try if already `possible`!

---

## 8. Parse a CV without screening
### Query
"Only parse this new CV and store the structured data. Do not run screening."
### Expected behavior
Supervisor identifies that parsing is needed but screening is not requested.  
Supervisor routes to the CV Screening agent or dedicated parser if available.  
Parser extracts structured data and writes it to the DB via DB Executor.  
Supervisor leaves candidate in the correct state without triggering screening logic.
### Notes / issues
- Worked without issues.

---

## 9. Follow up when no time slots were received
### Query
"The candidate has not replied with availability. Follow up with them."
### Expected behavior
Supervisor identifies the state awaiting_time_slots with no stored availability.  
Supervisor delegates a follow up email to the Gmail Agent.  
Gmail Agent sends the email through Gmail MCP.  
DB Executor records that a follow up was sent.  
Supervisor confirms the action.
### Notes / issues
- Works correctly. Asked DB Executor for email, then sent the email.

---

## 10. Resume a stuck candidate from checklist state
### Query
"This candidate is stuck. Resume from exactly where they left off."
### Expected behavior
Supervisor loads the stored checklist and candidate state via DB Executor.  
Supervisor identifies the next unchecked atomic step.  
Supervisor routes to the appropriate subagent for that specific step.  
Subagent performs the atomic action and DB Executor persists the update.  
Supervisor does not repeat completed steps or skip steps.
### Notes / issues
- It worked fine, but it took many attempts to set info in the database. Maybe more clear explanation is needed.

## 11. High level summary of all candidates
### Query
"Tell me a high level summary about all candidates that have "applied" but not yet moved on."
### Expected Behavior
Supervisor does not provide just the names, emails, or phone numbers.
Supervisor asks CV screener for info about the candidates.
### Notes / issues
- CV screener is having issues finding applicant CVs.
- Supervisor tried just giving names or contact info which is insufficient.