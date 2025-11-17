# ***`Gmail MCP – GCP Setup (Terraform + Bash)`***

This folder provisions the minimum GCP infrastructure to run the [Gmail MCP server](https://github.com/theposch/gmail-mcp/tree/main) without requiring billing:
- Creates (or adopts) a ***GCP project***
- Enables ***gmail.googleapis.com***
- Grants your user:
- `roles/editor`
- `roles/serviceusage.serviceUsageAdmin`
Prints console links to finish OAuth (consent screen + Desktop client)
> Billing is **not required** for Gmail API or OAuth Desktop client.

## ***Prerequisites***
- **Terraform** ≥ 1.6
- **gcloud** (optional but useful for verifying/importing projects)
- A Google account (you'll also add it as a **Test user** on the OAuth consent screen)

## Files
- `versions.tf` – provider & Terraform version pins
- `providers.tf` – Google provider config (uses project_id and region)
- `variables.tf` – input variables
- `main.tf` – project, Gmail API enablement, IAM bindings
- `outputs.tf` – project IDs and console URLs
- `terraform.tfvars` – team defaults (simple `key = "value"` pairs)

Example `terraform.tfvars`:
```python
project_id   = "gradio-hackathon-25"
project_name = "Gradio Agent MCP Hackathon 25"
user_email   = "hr.cjordan.agent.hack.winter25@gmail.com"
# region    = "europe-west3" # optional
```

## ***Quick Start (recommended: use the scripts)**
From the ***repo root***:
1. **Authenticate gcloud + ADC**
```bash
chmod +x scripts/gcp_setup.sh
./scripts/gcp_setup.sh
```

2. **Apply Terraform with smart defaults + auto-import**
```bash
chmod +x scripts/terraform_apply.sh
./scripts/terraform_apply.sh
```

- The script **prompts** for `project_id`, `project_name`, `user_email`.
- Press ***Enter*** to use defaults from `terraform/terraform.tfvars`.
- If the project already exists, it is **auto-imported** to avoid `409 alreadyExists`.

---

## ***Manual Usage (alternative)***
Run these from this `terraform/` directory:
```bash
terraform init

# If the project already exists, import it so Terraform manages it:
# terraform import google_project.project <your-project-id>

terraform apply
```

Override values:

```bash
terraform apply \
  -var="project_id=my-mcp-project" \
  -var="project_name=My MCP Project" \
  -var="user_email=you@example.com"
```

Or via env vars:
```bash
export TF_VAR_project_id="my-mcp-project"
export TF_VAR_project_name="My MCP Project"
export TF_VAR_user_email="you@example.com"
terraform apply
```

## **Outputs**
- `project_id` / `project_number`
- `gmail_api_service` — `"gmail.googleapis.com"` (resource present ⇒ enabled)
- `console_oauth_consent_screen_url` — configure consent (External, Test user, add scope)
- `console_oauth_credentials_url` — create ***OAuth 2.0 Client ID*** (Desktop app)

## **Final OAuth Setup (one-time, in Console)**

Terraform cannot create the **OAuth consent screen** or **Desktop OAuth client**, so you'll do these two steps once in the Google Cloud Console.  
This setup allows your **local Gmail MCP server** to access Gmail via OAuth securely.

> 💡 **Tip:** In the new Google Cloud UI, the old “Scopes” and “Test users” tabs are now under **Data access** and **Audience** in the left sidebar.

---

### 1️⃣ **Configure the OAuth Consent Screen**

**Purpose:** Identify your app to Google and specify who can use it during testing.

1. Open the link printed in Terraform outputs:  
   → `console_oauth_consent_screen_url`

2. If prompted, choose **User type: External**, then click **Create**.

3. Fill out **App info**:
   - **App name:** `Gmail MCP Local`
   - **User support email:** your Gmail address  
   - **Developer contact email:** your Gmail address  
   - Click **Save and Continue**

4. In the left sidebar, go to **Data access**
   - Click **Add or remove scopes**
   - Add the following scopes:
     ```text
     https://www.googleapis.com/auth/gmail.modify
     openid
     https://www.googleapis.com/auth/userinfo.email
     ```
     ✅ *These provide read, send, and modify access — no extra Gmail scopes required.*

5. Go to **Audience** (left sidebar)
   - Under **Test users**, click **Add users**
   - Add your Gmail account address  
   - Click **Save**

6. Go to **Summary** and confirm:
   - User type → **External**
   - Publishing status → **Testing**
   - Test users → your Gmail account
   - Scopes → shows Gmail modify, openid, userinfo.email

---

### 2️⃣ **Create a Desktop OAuth Client**

**Purpose:** This provides the credentials your **local MCP server** uses to initiate the OAuth flow.

1. Open the second Terraform output link:  
   → `console_oauth_credentials_url`

2. Click **Create credentials → OAuth client ID**

3. Choose:
   - **Application type:** `Desktop app`
   - **Name:** `gmail-mcp-desktop`

4. Click **Create**, then **Download JSON**, and move it into the expected directory:
```bash
mkdir -p ~/.gmail-mcp
mv ~/Downloads/client_secret_*.json ~/.gmail-mcp/credentials.json
```

### ⚠️ ***Important: Two Different JSONs***

- The file from:
```bash
gcloud auth application-default login
```
is your ***Application Default Credentials (ADC)*** — used by Terraform and `gcloud`.
It is ***not*** the same as the Desktop OAuth client JSON.
The Gmail MCP server requires the ***Desktop OAuth client JSON*** you downloaded.
→ Place it at `~/.gmail-mcp/credentials.json`.

### 🚀 ***When You Run the MCP Server***
The server will open a browser window asking you to sign in and approve access.
You'll see your app name (`Gmail MCP Local`) and the Gmail modify scope.
After approving, tokens are cached locally (usually `~/.gmail-mcp/token.json`), so you won't need to approve again.


---

### ⚙️ **Install Required Tools**

Before testing or running the Gmail MCP server, make sure the following tools are installed:

#### 🟣 1. Install `uv`
`uv` is a fast Python package manager used to run the Gmail MCP server.

Check if it's already installed:
```bash
uv --version
```
If not, install it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify:
```
uv --version
```
#### 🟠 2. Install Node.js (includes `npm` and `npx`)
npx is used to run the MCP Inspector, which lets you test your Gmail MCP server locally.
```bash
brew install node
```

### 🧪 ***Testing Locally with MCP Inspector***
Once toBefore connecting to Claude Desktop or a LangGraph agent, you can visually inspect and test your Gmail MCP server using the ***MCP Inspector*** web UI.

#### 1️⃣ **Run with simple path (direct server entry)**
Use this if you're already inside the ``gmail-mcp directory or the script path resolves cleanly:
```bash
npx @modelcontextprotocol/inspector uv run /Users/sebastianwefers/Desktop/development/recruitment-agent-mcp-hackathon-winter25/src/mcp_servers/gmail-mcp/src/gmail/server.py \
  --creds-file-path ~/.gmail-mcp/credentials.json \
  --token-path ~/.gmail-mcp/token.json
```

#### 2️⃣ **Run with full project context (recommended)**
This variant is more robust and works regardless of your working directory, because it explicitly tells `uv` which project directory to use and where your binaries are.

```bash
npx @modelcontextprotocol/inspector \
  /Users/sebastianwefers/.local/bin/uv \
  --directory /Users/sebastianwefers/Desktop/development/recruitment-agent-mcp-hackathon-winter25/src/mcp_servers/gmail-mcp \
  run gmail \
  --creds-file-path ~/.gmail-mcp/credentials.json \
  --token-path ~/.gmail-mcp/token.json
```

#### 🔍 What Happens
When you run either command, you should see output similar to:
```bash
Starting MCP inspector...
⚙️ Proxy server listening on localhost:6277
🔑 Session token: 8498939effc01e03c1b879efa72768e45608056ef1ad45e5c80344a7d9362a72
   Use this token to authenticate requests or set DANGEROUSLY_OMIT_AUTH=true to disable auth

🚀 MCP Inspector is up and running at:
   http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=8498939effc01e03c1b879efa72768e45608056ef1ad45e5c80344a7d9362a72

🌐 Opening browser...

```

This automatically opens a local browser window to the MCP Inspector UI, connected to your Gmail MCP server.

✅ Expected behavior:
- On first run, a browser window will prompt you to log in and approve access.
- After successful OAuth, a token file will be created:
```bash
~/.gmail-mcp/token.json
```
- Subsequent runs reuse this token — no re-auth required.
- You can now explore, invoke, and inspect your Gmail MCP tools visually (e.g., `listEmails`, `sendEmail`, `modifyLabel`, etc.) right from the web UI.

### 💻 ***Connecting the Gmail MCP Server to Claude Desktop***
1. Open your Claude Desktop configuration file:
```bash
nano ~/Library/Application Support/Claude/claude_desktop_config.json
```
2. Add this block (update paths if necessary):
```json
{
  "mcpServers": {
    "gmail": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/sebastianwefers/Desktop/development/recruitment-agent-mcp-hackathon-winter25/src/mcp_servers/gmail-mcp",
        "run",
        "gmail",
        "--creds-file-path",
        "/Users/sebastianwefers/.gmail-mcp/credentials.json",
        "--token-path",
        "/Users/sebastianwefers/.gmail-mcp/token.json"
      ]
    }
  }
}
```
3. Save the file and restart Claude Desktop.

4. Open ***Settings → Model Context Protocol → Add Server***, then connect to gmail.

Claude will now be able to:
- 📥 Read emails
- ✉️ Compose drafts
- 🏷 Send and modify Gmail messages directly from your account.

— all directly via your Gmail MCP server.


## 🧩 Why Deleting token.json Fixes the “invalid_grant” Error
The error occurs because the stored refresh token in token.json is expired or revoked, so Google rejects all refresh attempts.
Deleting the file forces the app to start a new OAuth flow, prompting you to log in again and generating a new, valid refresh token — which restores access to the Gmail API.

```bash
# 1. Remove the invalid cached token
rm /Users/sebastianwefers/Desktop/projects/recruitment-agent-mcp-hackathon-winter25/secrets/gmail-mcp/token.json


# 2. Re-run the Gmail MCP server (which triggers OAuth again)
python -m src.mcp_servers.gmail_mcp
```

Then, when the script printed a Google sign-in URL, you:
1. Opened it in your browser,
2. Logged in to your Google account,
3. Approved the Gmail API access,
4. And the new valid token.json was automatically recreated at:
```bash
~/.gmail-mcp/token.json
```