# Context Engineering 🧠

> Keeping long-running agents "forever young" by managing their memory.

## The Problem

LLMs have finite context windows. As conversations grow, you eventually hit the token limit and the agent breaks. Simply truncating old messages loses valuable context.

## The Solution: Compactive Summarization

Instead of truncating, we **summarize** old conversation history into a compact narrative, preserving the essential context while freeing up tokens.

```
┌─────────────────────────────────────────────────────────┐
│  Before Compaction (500+ tokens)                        │
├─────────────────────────────────────────────────────────┤
│  [System] You are an HR assistant...                    │
│  [Human] Show me all candidates                         │
│  [AI] Here are 5 candidates: Alice, Bob...              │
│  [Human] Tell me about Alice                            │
│  [AI] Alice is a senior engineer with 5 years...        │
│  [Human] Schedule an interview with her                 │
│  [Tool] Calendar event created...                       │
│  [AI] Done! Interview scheduled for Monday.             │
│  [Human] Now check Bob's CV                      ← new  │
└─────────────────────────────────────────────────────────┘
                         ↓ COMPACTION ↓
┌─────────────────────────────────────────────────────────┐
│  After Compaction (~200 tokens)                         │
├─────────────────────────────────────────────────────────┤
│  [System] You are an HR assistant...                    │
│  [AI Summary] User reviewed candidates, focused on      │
│       Alice (senior engineer), scheduled interview      │
│       for Monday.                                       │
│  [Human] Now check Bob's CV                      ← kept │
└─────────────────────────────────────────────────────────┘
```

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                  CompactingSupervisor                    │
│  ┌────────────────────────────────────────────────────┐  │
│  │  1. Intercept agent execution                      │  │
│  │  2. Run agent normally                             │  │
│  │  3. Count tokens after response                    │  │
│  │  4. If over limit → trigger compaction             │  │
│  └────────────────────────────────────────────────────┘  │
│                          │                               │
│                          ▼                               │
│  ┌────────────────────────────────────────────────────┐  │
│  │              HistoryManager                        │  │
│  │  • compact_messages() → LLM summarization          │  │
│  │  • replace_thread_history() → checkpoint update    │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

## 🔒 Subagents and Memory Safety

Compaction affects **only the supervisor’s `messages` channel** inside LangGraph’s checkpoint.

This includes:

- User messages  
- Supervisor AI messages  
- **Tool call and Tool result messages** (because these are part of the supervisor’s visible conversation history)

This does **not** include:

- Sub-agent internal reasoning  
- Sub-agent private memory  
- Hidden chain-of-thought  
- Any messages stored in sub-agent–specific channels

Only the messages that the supervisor itself receives are ever compacted.  
No internal sub-agent state leaks into the compacted summary.


## Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `token_limit` | 500 | Trigger compaction when exceeded |
| `compaction_ratio` | 0.5 | Fraction of messages to summarize |

### Compaction Ratio Explained

The `compaction_ratio` controls how aggressively we summarize:

```
compaction_ratio = 0.5 (Default)
├── Summarizes: oldest 50% of messages
└── Keeps verbatim: newest 50% of messages

compaction_ratio = 0.8 (Aggressive)
├── Summarizes: oldest 80% of messages  
└── Keeps verbatim: only newest 20%
    → Use when context is very tight

compaction_ratio = 0.2 (Gentle)
├── Summarizes: only oldest 20%
└── Keeps verbatim: newest 80%
    → Use when you want more history preserved
```

**Example with 10 messages:**
- `ratio=0.5` → Summarize messages 1-5, keep 6-10 verbatim
- `ratio=0.8` → Summarize messages 1-8, keep 9-10 verbatim
- `ratio=0.2` → Summarize messages 1-2, keep 3-10 verbatim

## Usage

```python
from src.context_eng import compacting_supervisor

# Just use it like a normal agent - compaction is automatic!
response = compacting_supervisor.invoke(
    {"messages": [HumanMessage(content="Hello")]},
    config={"configurable": {"thread_id": "my-thread"}}
)

# Streaming works too
for chunk in compacting_supervisor.stream(...):
    if chunk["type"] == "token":
        print(chunk["content"], end="")
```

## LangGraph Integration

### How It Wraps the Agent

The `CompactingSupervisor` uses the **Interceptor Pattern** - it wraps the existing LangGraph agent without modifying it:

```python
# In compacting_supervisor.py
from src.agents.supervisor.supervisor_v2 import supervisor_agent, memory

compacting_supervisor = CompactingSupervisor(
    agent=supervisor_agent,      # ← Original LangGraph agent
    history_manager=HistoryManager(memory_saver=memory),  # ← LangGraph's MemorySaver
    ...
)
```

The agent itself is **unchanged**. We just intercept `invoke()` and `stream()` calls.

### How It Manipulates LangGraph Memory

LangGraph uses **checkpoints** to persist conversation state. Normally, messages are append-only. Our `HistoryManager.replace_thread_history()` bypasses this to force a rewrite:

```
Normal LangGraph flow:
┌─────────────────────────────────────┐
│  Checkpoint Storage (MemorySaver)   │
│  ┌───────────────────────────────┐  │
│  │ messages: [m1, m2, m3, m4...] │  │  ← Append-only
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘

After compaction (we override):
┌─────────────────────────────────────┐
│  Checkpoint Storage (MemorySaver)   │
│  ┌───────────────────────────────┐  │
│  │ messages: [sys, summary, m4]  │  │  ← Force-replaced!
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Key mechanism in `replace_thread_history()`:**
1. Get current checkpoint via `memory.get_tuple(config)`
2. Build new checkpoint with compacted messages
3. Increment version + update timestamps
4. Write directly via `memory.put(...)` - bypassing normal reducers

This is a **low-level override** of LangGraph's internal checkpoint format. It works because we maintain the expected checkpoint structure (`channel_versions`, `channel_values`, etc.).

## Files

| File | Purpose |
|------|---------|
| `token_counter.py` | Count tokens in message lists |
| `history_manager.py` | Summarization + checkpoint manipulation |
| `compacting_supervisor.py` | Agent wrapper (Interceptor Pattern) |

