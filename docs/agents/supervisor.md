# Supervisor Agent Overview
This document explains the role, behavior, and context-engineering strategy of the Supervisor Agent used in the agentic HR recruitment system. It describes how the supervisor plans, coordinates, delegates, and adapts the multi-agent workflow, and how context is compressed, summarized, and managed to maintain robustness across long-running interactions.

It also explains context-engineering strategies that are utilized in order to reduce token usage along with increasing reliability and task completion rate of the agents.

---

## 1. Purpose of the Supervisor Agent
The Supervisor Agent serves as the centralized orchestrator responsible for maintaining global workflow control. Its role is to ensure that each subagent operates in the correct order, under the correct conditions, with the right context, and with full visibility into progress and failures.

At a high level, the supervisor is responsible for:
- Generating and maintaining the end-to-end hiring plan.
- Determining which subagent should execute next.
- Providing stateful context to each subagent.
- Performing adaptive re-planning when outputs or conditions change.
- Managing memory summaries and preventing context pollution.
- Producing explainable logs and reasoning traces for the dashboard.

This agent ensures that the entire HR pipeline behaves autonomously while remaining transparent, safe, and resilient.

---

## 2. High-Level Workflow
The supervisor follows a structured, plan-driven execution model. The default plan is:

1. CV Screening
2. Voice Screening
3. HR Interview Scheduling
4. Final Decision Report

However, execution is not strictly linear. The supervisor can skip, re-order, repeat, or halt steps based on subagent outputs.

### Workflow Model
1. **Initialize Plan**
   - Build an initial sequence of workflow stages based on available candidate data.
   - Load any relevant memory summaries or past runs from the database.

2. **Select Next Stage**
   - Evaluate current state.
   - Choose the next subagent based on plan progress and real-time results.

3. **Construct Subagent Context Package**
   - Provide the subagent with the minimal context they need:
     - Candidate details
     - Results from prior stages
     - Relevant memory summaries
     - Tool call history (when helpful)
     - Current workflow goal

4. **Invoke the Subagent**
   - The selected agent executes a task using LangGraph tool calls or MCP integrations.
   - Outputs are validated and stored in state and database.

5. **Reflect and Update Plan**
   - The supervisor generates a lightweight reflection summary:
     "What happened?", "Is the result valid?", "What is needed next?"
   - If conditions changed, the supervisor updates the plan accordingly.
     Examples:
     - Skip voice screening if CV screening fails.
     - Retry scheduling if the calendar shows no available slots.
     - Pause and request HR confirmation when required.

6. **Persist Memory**
   - Summaries, transcripts, evaluations, and structured results are stored to prevent context bloating.
   - Only relevant compact memory is injected back into future steps.

7. **Repeat Until Complete**

---

## 3. Task Delegation Strategy
The supervisor delegates tasks to subagents based on rule-based planning combined with lightweight LLM reasoning.

### Delegation Logic
- **CV Screening Agent** is invoked when a new applicant is added or a CV is updated.
- **Voice Screening Agent** is invoked when the candidate passes CV screening and HR or the plan flags them as suitable for a phone screen.
- **Scheduler Agent** is invoked once voice screening produces a valid transcript and evaluation.
- **Decision Agent** is invoked after all stages complete, or when early rejection is clear.

Each subagent returns structured outputs that the supervisor uses to drive the next step.

---

## 4. Adaptive Re-Planning
One of the supervisor’s core responsibilities is to respond dynamically to real-world conditions.

Examples of adaptive behaviors:

- **Tool failure**: If Gmail or Calendar returns an MCP error, the supervisor retries, selects an alternative interaction path, or defers the step.
- **Calendar constraints**: If no timeslots are available, the supervisor generates an alternate plan.
- **Candidate status shifts**: If a candidate responds late or provides new documents, the supervisor reevaluates the plan.
- **Voice call failure**: If the candidate does not pick up, the supervisor schedules a retry or sends an email follow-up.

This makes the workflow robust, autonomous, and consistent with agentic paradigms.

In unique situations, such as exceptional applicants, the agent can accellerate the timeline such as skipping stages. This is entirely discretionary and up to the agent's decision.

---

## 5. Context Engineering Strategy
We utilize context engineering many times in the workflow. Each subagent instance is stateless, meaning that it doesn't retain any memory or context from previous turns. This allows for reduced token usage, since information from previous applicants is not relevant for new tasks. This state is reset every time it handles a unique task, but is retained until the supervisor determines the subagent has fully completed all necessary steps.

Each time a subagent completes a task, the agent is given the full response. After the supervisor performs its next action, the subagent response is compacted into a high-level summary.

The supervisor agent itself is also stateless in a sense: its context is applicant-dependant. Real-life timelines are messy, and multiple applicants will have steps overlap. Each time the supervisor agent needs to perform a new task, it loads the context from the user it is working on, and unloads it when it is done. This way, the supervisor is able to stay focused on a specific applicant and not get confused or distracted by managing multiple applicants at the same time. The state for this agent is saved in temporary files which are deleted once the applicant has a final decision made (hire or discard).

---

## 6. Explainability and Dashboard Integration
The supervisor produces the trace outputs that power the Gradio dashboard.

This includes:
- Plan state (past, current, future)
- Tool call logs
- Reasoning and reflection summaries
- Active memory excerpts
- Subagent outputs
- Error messages and fallback paths

Because a single agent manages the plan, dashboard integration remains consistent and interpretable.