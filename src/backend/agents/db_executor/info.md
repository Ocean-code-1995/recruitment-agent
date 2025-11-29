This agent coding agent based `CodeAct`agent pattern, see:
https://github.com/langchain-ai/langgraph-codeact


Test as follows:

>>> cd /Users/sebastianwefers/Desktop/projects/recruitment-agent

>>> docker compose -f docker/docker-compose.yml up --build candidates_db_init


# Make sure your OpenAI key is available to the process
>>> export OPENAI_API_KEY=sk-...   # or however you normally set it

# Override host so the Python code connects to localhost, not 'db' and run "db_executor"
>>> POSTGRES_HOST=localhost POSTGRES_PORT=5433 python -m src.agents.db_executor.db_executor


# DEBUG attempt
------------------------------------------------------------------------------------
- works:
POSTGRES_HOST=localhost POSTGRES_PORT=5433 python src/agents/db_executor/debug_db_connection.py