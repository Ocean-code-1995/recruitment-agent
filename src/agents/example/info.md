### How to Run the LangGraph Reasoning Monitoring Demo Agent

1. Make sure to have the following installed
```bash
pip install -r requirements/dev.txt
```

2. Set TAVILY_API_KEY:
- link: https://www.tavily.com

3. Run the following from repo root:
```bash
export PYTHONPATH=./src
langgraph dev
```
This loads the root-level `langgraph.json` and makes all agents available in LangGraph Studio.

4 Open the Studio UI
After the server starts, open:
```bash
https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```
**NOTE:** Open it in anything, but safari!

Select the agent named react_agent (or whichever your config specifies).

---

### Demo Prompt to Use
Paste the following into the Studio console:
```txt
First search for the current temperature in Fahrenheit in Cape Town, South Africa.
Then convert that temperature to Celsius using the conversion tool.
```

***This triggers:***
1. A Tavily search for the current Fahrenheit temperature
2. A tool call to convert Fahrenheit → Celsius
3. Full ReAct reasoning + tool trace in the UI

---

### ⚙️ Multiple Agents in langgraph.json
You can expose multiple agents to LangGraph Studio by listing them under the graphs section of your root `langgraph.json`.

Example:
```json
{
  "dependencies": ["src"],
  "graphs": {
    "react_agent": "agents.example.react_agent:agent",
    "cv_screener": "agents.cv_screening.screener:agent",
    "supervisor": "agents.supervisor.supervisor:agent"
  }
}
```
Each entry maps:
```bash
"graph_name": "module.path:object_name"
```

Where:
- `graph_name` → appears in LangGraph Studio
- `module.path` → Python import path under `src/`
- `object_name` → the variable that contains the graph/agent
This allows one project to host many agents simultaneously (e.g., supervisor, tools agent, CV-screening agent, etc.).
