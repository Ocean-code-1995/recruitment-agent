# Prompt Management System

This module provides a centralized way to manage prompts using **PromptLayer** with a local filesystem fallback. It allows you to version prompts, manage environments (dev/staging/prod), and easily switch between local development and cloud-managed prompts.

## 🚀 Usage

Import the `get_prompt` function to load prompts anywhere in your application.

```python
from src.backend.prompts import get_prompt
```

### 1. Load from PromptLayer (Default)
By default, if `PROMPTLAYER_API_KEY` is set in your environment, it will fetch the prompt from PromptLayer using the configured environment label (default: `production`).

```python
# Fetches 'DB_Executor' tagged with current environment (e.g., 'production')
system_prompt = get_prompt("DB_Executor")
```

### 2. Load Latest Version (Ignore Environment)
Useful for testing or when you want to ensure you have the absolute latest saved version from PromptLayer, ignoring any 'prod' or 'dev' tags.

```python
# Fetches the absolute latest version of the template
system_prompt = get_prompt("DB_Executor", latest_version=True)
```

### 3. Force Load from Local File
You can force loading from a local file, which is useful for local development without an internet connection or for testing new prompts before pushing to PromptLayer.

```python
# Loads from src/prompts/templates/db_executor/v1.txt
# (Assuming 'v1.txt' is the file name in that directory, or provide full path)
system_prompt = get_prompt("db_executor/v1", local_prompt_path="src/prompts/templates")
```

If you don't provide a `local_prompt_path` but also don't have a `PROMPTLAYER_API_KEY` set, it defaults to looking in `src/prompts/templates`.

## 📂 Directory Structure

Store your local prompt backups in `src/prompts/templates/`.

```
src/prompts/
├── __init__.py          # Exposes get_prompt
├── prompt_layer.py      # Core logic
├── templates/           # Local prompt storage
│   ├── db_executor/
│   │   └── v1.txt
│   ├── supervisor/
│   │   └── v1.txt
│   └── ...
└── info.md              # This file
```

## ⚙️ Configuration

- **`PROMPTLAYER_API_KEY`**: Set this env var to enable PromptLayer.
- **`PROMPT_ENVIRONMENT`**: Set to `dev`, `staging`, or `production` (default) to control which tagged version is loaded.

## 🔍 Debugging

The system prints clear logs to stdout so you know where your prompt came from:

- `📋 Loaded prompt '...' from PromptLayer (env=production)`
- `📋 Loaded prompt '...' from PromptLayer (latest version)`
- `📄 Loaded prompt '...' from local file: ...`

