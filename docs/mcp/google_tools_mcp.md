# Google Calendar and GMail Tools / MCP

## 1) ***`Base setup`***
### 1.1) ***GMail Account***

### 1.2) ***Google Cloud***

#### Terraform Modifications (Minimal)
You can extend your existing Gmail Terraform to include Calendar support.
Add these to your `main.tf`:
```bash
# Enable the Google Calendar API
resource "google_project_service" "calendar_api" {
  project = google_project.project.project_id
  service = "calendar.googleapis.com"
  disable_on_destroy = false
}
```
And if you want, you can add an output for convenience:
```bash
output "console_calendar_api_url" {
  value = "https://console.cloud.google.com/apis/library/calendar.googleapis.com?project=${google_project.project.project_id}"
}
```
After adding, re-run your scripts:
```bash
cd terraform
terraform apply
```
This enables the Calendar API in the same project your Gmail MCP is using — so you don't have to create a second one.

Terraform will:
1. Detect that you already have a project and Gmail API from before.
2. Notice the new Calendar API resource in ``main.tf.
3. Apply only that new change (plus any small diff in IAM roles if needed).

💡 What Happens Internally
When you run `terraform apply`, Terraform will:
- Read your current state file (`terraform.tfstate`).
- Query GCP to check what's already deployed.
- Compute a plan (the difference between your state and the `.tf` files).

#### 🔑 OAuth Setup — Shared Consent Screen
You do not need a new consent screen — just reuse your existing one (Gmail MCP Local) and add the Calendar scope.

Go to:
👉 [Google Cloud Console → APIs & Services → OAuth consent screen → Edit app → Data access → Add scopes]
Add this scope:
```arduino
https://www.googleapis.com/auth/calendar
```
You'll now have Gmail + Calendar under one consent.
Then, create a ***second OAuth client***:
Application type: Desktop app
Name: `calendar-mcp-desktop`
Download the credentials JSON → save it to:
```bash
~/.calendar-mcp/credentials.json
```
The Calendar MCP server will then use this credentials file when it first authenticates.

#### 🧩  MCP Client Config (Claude or LangGraph)
Just add a new block alongside your Gmail entry.
For Claude Desktop (`claude_desktop_config.json`)
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
    },
    "google_calendar": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/sebastianwefers/Desktop/development/recruitment-agent-mcp-hackathon-winter25/src/mcp_servers/calendar-mcp",
        "run",
        "calendar"
      ]
    }
  }
}
```

For LangGraph:
```python
client = MultiServerMCPClient({
    "gmail": {
        "command": "uv",
        "args": [
            "--directory", "/Users/sebastianwefers/Desktop/development/recruitment-agent-mcp-hackathon-winter25/src/mcp_servers/gmail-mcp",
            "run", "gmail",
            "--creds-file-path", "/Users/sebastianwefers/.gmail-mcp/credentials.json",
            "--token-path", "/Users/sebastianwefers/.gmail-mcp/token.json"
        ],
        "transport": "stdio"
    },
    "google_calendar": {
        "command": "uv",
        "args": [
            "--directory", "/Users/sebastianwefers/Desktop/development/recruitment-agent-mcp-hackathon-winter25/src/mcp_servers/calendar-mcp",
            "run", "calendar"
        ],
        "transport": "stdio"
    }
})
```
#### Environment Variables (.env)
Create the .env in your calendar-mcp repo root, just like described in its README:
```bash
GOOGLE_CLIENT_ID='YOUR_CLIENT_ID'
GOOGLE_CLIENT_SECRET='YOUR_CLIENT_SECRET'
TOKEN_FILE_PATH='.gcp-saved-tokens.json'
OAUTH_CALLBACK_PORT=8080
CALENDAR_SCOPES='https://www.googleapis.com/auth/calendar'
```
⚠️ Make sure the redirect URI matches:
```bash
http://localhost:8080/oauth2callback
```
You'll go through one browser OAuth login on first run, and then `.gcp-saved-tokens.json` will be created — no need to repeat.


## 2) ***`Model Context Protocol`***
**References**
- [Official MCP Docs](https://modelcontextprotocol.io/docs/getting-started/intro)
- [MCP Crash Course by YouTuber & AI Engineer Dave Ebbelaar](https://www.youtube.com/watch?v=5xqFjh56AwM&t=761s)
- *Existing Repo's*
  - [Curated list of MCP servers](https://github.com/modelcontextprotocol/servers) hosted by `MCP` themselves.
  - [Goole Calendar](https://github.com/deciduus/calendar-mcp/blob/main/README.md)
  - calendar repo alterntives:
    - https://github.com/nspady/google-calendar-mcp/tree/main/src/tools
```psql
# Calendar MCP (Dual Layer)
LLM Agent
   │
   │  JSON-RPC over STDIO
   ▼
MCP Bridge (mcp_bridge.py)
   │  HTTP requests to localhost:8000
   ▼
FastAPI Server (server.py)
   │
   └── Google Calendar API (OAuth + REST)
```

  - [GMail](https://github.com/theposch/gmail-mcp/blob/main/README.md)
```psql
    # Gmail MCP (Pure MCP)
LLM Agent
   │
   │  JSON-RPC over STDIO
   ▼
Gmail MCP Server
   │
   └── Gmail API (OAuth + REST)
```
  - [Gmail](https://github.com/MCP-Mirror/Samarth2001_gmail-mcp)
  - [Gmail](https://github.com/jasonsum/gmail-mcp-server)


## 🧱 1️⃣ Compatibility Breakdown
| Area                | Gmail MCP                                      | Calendar MCP                                    | Compatible? | Notes                                                                       |
| ------------------- | ---------------------------------------------- | ----------------------------------------------- | ----------- | --------------------------------------------------------------------------- |
| **Transport**       | MCP via STDIO                                  | MCP via STDIO (through FastAPI bridge)          | ✅           | Works out of the box with same client setup.                                |
| **Auth Type**       | OAuth 2.0 Desktop Client                       | OAuth 2.0 Desktop Client                        | ✅           | Identical flow; can reuse same consent screen + test users.                 |
| **Scopes**          | `https://www.googleapis.com/auth/gmail.modify` | `https://www.googleapis.com/auth/calendar`      | ✅           | Different scopes, but both can live under one consent screen.               |
| **Terraform**       | Creates project, enables Gmail API, sets roles | Just needs Calendar API enabled too             | ✅           | Add one more API + scope to Terraform config.                               |
| **Token Storage**   | `~/.gmail-mcp/token.json`                      | `.gcp-saved-tokens.json`                        | ✅           | Each uses its own token file; keep separate to avoid refresh token mix-ups. |
| **Runtime**         | `uv` stdio server                              | `python run_server.py` (auto-switches to stdio) | ✅           | You can use `uv` for both, if you prefer consistency.                       |
| **MCP Integration** | Claude / LangGraph via config                  | Same                                            | ✅           | Just add another entry under `mcpServers`.                                  |
