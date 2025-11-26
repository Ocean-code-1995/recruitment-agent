# ⚙️ Tools Required for MVP (Phases 1–5)

The system consists of a **Supervisor Agent** (central orchestrator) and several **specialized subagents**.  
Each tool corresponds to a specific capability needed for the single-candidate MVP flow — from CV upload to interview scheduling.

---

## 🧠 **Supervisor Agent (Core Orchestrator)**

### **Role**
Acts as the **central controller**:
- Interfaces with HR (via UI or chat)
- Handles reasoning, status reporting, and command interpretation
- Orchestrates subagents (screening, Gmail, calendar)
- Updates both the database and checklist after each atomic action

### **Tools Required**

| Tool | Purpose | Used in Phase |
|------|----------|---------------|
| 🗃️ **Database Tool / ORM Adapter** | Read, create, and update `Candidate` records (status, CV paths, results). | 1–5 |
| 📄 **File I/O Tool** | Read/write per-candidate checklist and parsed CV files. | 1–5 |
| 📊 **Reporting Helper / Aggregation Utility** | Query DB and summarize candidate counts (new, screened, passed, failed). | 2 |
| 🧩 **Subagent Dispatch Interface** | Send structured tasks to subagents (screening, Gmail, calendar). | 3–5 |
| 🧱 **State Manager** | Load and update candidate’s deterministic state object (`state`, `checklist`, `status`). | 4–5 |
| 🕵️ **HR Command Parser / Intent Handler** | Interpret HR’s natural-language instructions (e.g., “process new applicants”). | 2 |

---

## 🤖 **Subagents & Their Tools**

### **1. CV Screening Subagent**
**Phase:** 3  
**Purpose:** Automatically screen and score CVs.

| Tool | Purpose |
|------|----------|
| 📄 **CV Parser** | Extract structured text from uploaded CV (PDF/DOCX). |
| 🧮 **Screening Model / Classifier** | Evaluate parsed CV using rules or an ML/LLM-based model. |
| 🗃️ **DB Access Tool** | Save screening results and update `Candidate.status = cv_screened`. |
| 📄 **Checklist Writer** | Mark `[x] Screening started` and `[x] Screening completed` in the checklist. |

---

### **2. Gmail Subagent**
**Phase:** 4  
**Purpose:** Send automated emails to candidates based on screening results.

| Tool | Purpose |
|------|----------|
| 📬 **Gmail API Wrapper** | Send templated emails (rejection or invitation). |
| 🧠 **Template Manager** | Store and select appropriate email templates. |
| 🗃️ **DB Access Tool** | Record email activity and update candidate state. |
| 📄 **Checklist Writer** | Mark `[x] Candidate notified` and `[x] Email status recorded`. |

---

### **3. Calendar / Scheduling Subagent**
**Phase:** 5  
**Purpose:** Automate interview scheduling for passed candidates.

| Tool | Purpose |
|------|----------|
| 🗓️ **Google Calendar API Wrapper** | Retrieve HR availability and create interview events. |
| 📬 **Gmail API (reuse)** | Send scheduling confirmations and time slot requests. |
| 🧠 **Availability Matcher** | Compare candidate-provided slots vs HR calendar availability. |
| 🗃️ **DB Access Tool** | Update `Candidate.status = interview_scheduled`. |
| 📄 **Checklist Writer** | Mark `[x] HR availability checked`, `[x] Interview scheduled`, `[x] Confirmation sent`. |

---

## 🧾 **Cross-Cutting Utilities (Shared by All Agents)**

| Utility | Purpose | Used by |
|----------|----------|----------|
| 🧩 **Checklist Manager** | CRUD operations on per-candidate Markdown checklist files (load, mark, persist). | All |
| 🧱 **State Sync Layer** | Sync checklist milestone boundaries with DB `status` updates. | Supervisor |
| ⏱️ **Logging & Audit Utility** | Record all actions, errors, and state transitions. | All |
| 🧮 **Config / Environment Loader** | Manage API keys, paths, and credentials for Gmail & Calendar. | All networked agents |

---

## 🧭 **Tool Overview by Phase**

| Phase | Supervisor Tools | Subagents / Tools |
|-------|-------------------|------------------|
| **1 — Candidate I/O + Storage** | DB Adapter, File I/O, Checklist Manager | CV Parser (manual for MVP) |
| **2 — Supervisor + UI** | HR Command Parser, DB Reporter, Checklist Manager | — |
| **3 — CV Screening** | Subagent Dispatcher, Checklist Manager | CV Parser, Screening Model, DB Writer |
| **4 — Candidate Communication** | Subagent Dispatcher, Checklist Manager | Gmail API, Template Manager |
| **5 — Interview Scheduling** | Subagent Dispatcher, Checklist Manager | Calendar API, Availability Matcher, Gmail API |

---

## ✅ **Summary**

- **Supervisor Agent Tools:**  
  - DB Adapter  
  - Checklist Manager  
  - HR Interface (UI or CLI)  
  - Subagent Dispatcher  
  - State Sync Logic  

- **Subagents:**  
  - **Screening Subagent:** CV Parser + Screening Model  
  - **Gmail Subagent:** Email Templating + Send API  
  - **Calendar Subagent:** Scheduling + Availability Matching  

Together, these tools form the complete single-candidate MVP pipeline —  
from candidate intake → CV screening → communication → interview scheduling.
