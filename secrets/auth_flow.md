### 🔐 Google MCP Auth Flow Summary

- **`credentials.json`** → App credentials (downloaded once from Google Cloud Console).  
- **`token.json`** → User-specific OAuth token (auto-created on first run).

---

### ⚙️ When & How It Happens

1. **At MCP startup:**  
   The script loads `credentials.json` (OAuth client info).  
2. **If no valid `token.json`:**  
   - Browser-based OAuth flow starts.  
   - You log in and grant access.  
   - A new `token.json` is saved locally.  
3. **On later runs:**  
   - The MCP reads the existing `token.json`.  
   - Automatically refreshes it if expired.  
   - No browser prompt needed.

---

### 🚫 Git Hygiene

- ❌ Never commit `token.json` to Git.  
- 👤 Each developer generates their own token.  
- 🖥️ For servers or CI → use a **service account** instead.
