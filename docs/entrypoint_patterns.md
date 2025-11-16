## 📄 How CV Parsing & LLM Evaluation Are Triggered — Summary

Below is a clean overview of the three architectural patterns for triggering **CV parsing** and **LLM-based CV evaluation** inside an agentic HR pipeline.

---

## 🧩 End-to-End Flow
1. Candidate uploads CV  
2. System stores candidate entry in DB  
3. CV parser runs automatically  
4. Parsed CV JSON is stored in DB  
5. Orchestrator detects that parsing is done  
6. Orchestrator triggers the CV Screening Agent  
7. LLM evaluates CV and stores results  
8. Pipeline continues (voice → scheduling → final decision)

---
```sql
[User (Streamlit UI)]
   ↓
   Upload CV + metadata (HTTP POST)
   ↓
[Orchestrator API]
   ↓
   Save CV file (local or cloud)
   ↓
   Write candidate entry to DB
   ↓
   Trigger parsing pipeline
   ↓
   Update parsed_cv_json + status='parsed'
   ↓
   Orchestrator runs CV Screening Agent
   ↓
   Write results to DB + status='cv_screened'
   ↓
[Streamlit polls /api/status/<candidate_id>]
   ↓
   Display updated status + scores
```
---

## 🧠 Pattern A — Orchestrator-Driven State Machine (Recommended)

The orchestrator continuously monitors the candidate’s status in the database and decides the next action based on that state.

**Flow:**  
- After parsing finishes, the system sets `status = "parsed"`  
- The orchestrator checks the state and sees that the next step is CV screening  
- It triggers the CV Screening Agent  
- Once evaluation completes, the system updates status to `status = "cv_screened"`  
- The orchestrator then moves to the next stage (voice screening, etc.)

**Why this is the best choice:**  
- Most “agentic” (planning + reasoning)  
- Clean separation between deterministic parsing and cognitive reasoning  
- Perfect fit for LangGraph orchestration  
- Easy to visualize reasoning and workflow progress  
- Ideal for hackathon judges (transparency + intentionality)

---

## 🧠 Pattern B — Event-Based Trigger (Webhook, Queue, Pub/Sub)

The parsing component emits an event like “cv_parsed” when finished.  
A listener or orchestrator receives that event and immediately triggers the CV Screening Agent.

**Pros:**  
- Scales well  
- Good for microservice architectures  

**Cons:**  
- Less agentic  
- Harder to show planning logic and state transitions  
- More infrastructure complexity

---

## 🧠 Pattern C — Orchestrator Polling the Database

A loop runs every few seconds, searching for candidates whose status is “parsed” and triggering CV evaluation when found.

**Pros:**  
- Very simple to implement  
- Works well for demos and prototypes  

**Cons:**  
- Not reactive  
- Less elegant  
- Not as agentic or clean as Pattern A

---

## 🏆 Recommendation

Use **Pattern A (Orchestrator-Driven State Machine)** for the hackathon submission.

**Benefits:**  
- Natural agentic behavior  
- Works directly with LangGraph’s planning style  
- Provides clear reasoning transparency  
- Fits well with your multi-agent architecture  
- Easy to show on the Gradio dashboard  
- Minimal complexity while still highly principled

---

## 📝 TL;DR

- CV parsing should run automatically after upload  
- Parsed data should be saved to the DB  
- **LLM CV evaluation should NOT be triggered by upload**  
- Instead, the **orchestrator detects the new state and triggers evaluation**  
- Pattern A (state machine) is the cleanest and most agentic solution