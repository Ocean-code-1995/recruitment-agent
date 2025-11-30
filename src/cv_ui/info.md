### 📄 CV Upload Stage — Overview

#### 🎯 Purpose
The **CV Upload Stage** is the **entry point** of the HR screening pipeline.  
It collects candidate information, stores the uploaded CV, and registers the applicant in the central database.  
This stage serves as the bridge between the **candidate** and the **agentic system**,  
initiating the automated recruitment workflow.

---

#### 🧩 Role in the Pipeline
| Step | Description | Responsible Component |
|------|--------------|-----------------------|
| 1️⃣ Candidate applies | Candidate fills out form and uploads CV via the web interface | **Streamlit UI** |
| 2️⃣ File saved | CV file is stored in the shared volume (`/src/database/cvs/uploads`) | **File handler (`save_cv`)** |
| 3️⃣ Candidate registered | Candidate details are inserted into the database | **DB client (`register_candidate`)** |
| 4️⃣ Status initialized | Candidate record created with `status = "applied"` | **Database (`candidates` table)** |

---

#### 🧱 Data Created
A new record is added to the **`candidates`** table containing:

| Field | Description |
|--------|--------------|
| `id` | Unique candidate UUID |
| `full_name` | Candidate’s full name |
| `email` | Unique email address |
| `phone_number` | Optional contact number |
| `cv_file_path` | Path to the uploaded CV file |
| `parsed_cv_json` | *Empty at this stage* |
| `status` | `"applied"` |
| `created_at` / `updated_at` | Automatic timestamps |

---

#### 🧠 Next Stage Triggered
Once a record exists with `status="applied"`,  
the **CV Parsing Agent** is automatically triggered to extract structured data  
(e.g., skills, education, and experience) from the uploaded CV.  
This marks the transition toward the **CV Screening** phase.

---

#### ✅ Key Takeaways
- **Initial entrypoint:** introduces candidates into the system.  
- **File persistence:** all uploaded CVs are stored locally for later parsing.  
- **Automation-ready:** triggers the next agent without human input.  
- **Simple interface:** Streamlit UI makes the process candidate-friendly.

> **In short:**  
> The CV Upload Stage is the **gateway** to the pipeline — it collects, stores, and initializes candidate data so the agentic workflow can proceed autonomously.
