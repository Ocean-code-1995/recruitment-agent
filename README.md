# ***HR Recruitment Agent***

![License](https://img.shields.io/badge/License-GPLv3-blue)
![Gradio](https://img.shields.io/badge/Gradio-Interface-FF6F00?logo=gradio&logoColor=orange)
![Hugging Face](https://img.shields.io/badge/Hugging_Face-Models-FFD21E?logo=huggingface&logoColor=yellow)

## Overview
This repository hosts our team's submission for **Track 2: MCP in Action** in the [MCP's 1st Birthday Hackathon](https://huggingface.co/MCP-1st-Birthday).

Our project is an autonomous HR recruitment agent that streamlines early-stage candidate screening by automating CV evaluation, voice interviews, and interview scheduling while keeping human decision-makers in the loop. Built on LangGraph for multi-agent orchestration and MCP for standardized tool integration with Gmail, Google Calendar, and Twilio APIs, this system demonstrates practical AI agents that handle real-world HR workflows end-to-end.

### Problem statement
Recruiting early-stage candidates is time-intensive and costly. HR teams spend approximately 40-60% of their screening time on repetitive tasks such as CV review, initial candidate assessments, and scheduling interviews. For companies receiving hundreds of applications per open role, this creates a bottleneck that delays hiring timelines by weeks and increases costs per hire. Additionally, early-stage screening often lacks consistency due to reviewer bias and fatigue, leading to qualified candidates being overlooked and poor cultural fits advancing to expensive in-person interviews.

### Our solution
This system automates the first 80% of the screening pipeline while maintaining human judgment where it matters most. By combining LLM-based CV evaluation, voice-based technical screening, and calendar integration, the agent reduces manual screening time from hours per candidate to minutes, lowering cost-per-hire by an estimated 60-70% while improving consistency and reducing time-to-hire by 2-3 weeks. Rather than replacing human decision-making, it compresses the tedious work into structured data and insights, freeing HR teams to focus on nuanced final decisions and candidate experience.

## How to use it
### Demo
TODO: Explain how to use it, such as through Gradio.

### Candidates
In a real deployment, candidates begin by uploading their CVs through a web portal. The system parses the CV into structured text and automatically evaluates it against the job description using an LLM, scoring skills match, experience alignment, and education fit. Candidates passing the CV screening threshold are invited to a voice screening interview conducted via Twilio, where a conversational agent asks relevant technical and culture-fit questions. The voice call is transcribed and analyzed for communication clarity and sentiment. Qualified candidates are then automatically scheduled for in-person interviews via Google Calendar, with email notifications sent through Gmail MCP integration. Throughout the process, all results (scores, transcripts, reasoning traces) are persisted in a PostgreSQL database, providing HR teams with a dashboard view of each candidate's progression. A final decision agent synthesizes all screening data into a concise report for human HR reviewers to make the ultimate hire/reject/maybe determination.

## How it works
The system is built on a multi-agent orchestration framework using LangGraph, where a main supervisor agent coordinates specialized subagents through the recruitment pipeline. Each agent is a distinct LLM-powered reasoning node that maintains conversation state, invokes tools, accesses external services, and passes context to other agents. This modular design enables each agent to specialize in its domain while the supervisor handles overall workflow planning and adaptation.

The main orchestrator agent serves as the entry point and maintains the overall recruitment workflow. It tracks candidate progress through the pipeline, decides which subagent to activate next, and handles re-planning if any step fails. For example, if no calendar slots are available, the orchestrator can delay scheduling or notify HR rather than simply failing. The CV Screening Agent evaluates candidate CVs against the job description using structured LLM reasoning. It parses uploaded documents using Docling to extract information, scores candidates across multiple dimensions (skills match, experience fit, education alignment, each on a 0-1 scale), and persists results to the database along with reasoning traces for full transparency. The Voice Screening Agent conducts automated phone interviews using Twilio for call management and Whisper for speech-to-text. It engages in multi-turn dialogue asking technical and culture-fit questions, analyzes sentiment and communication quality from transcripts, and generates structured evaluation reports. The Meeting Scheduler Agent integrates with Google Calendar and Gmail through MCP servers to automatically book HR interviews, handling availability checks, calendar conflicts, and email notifications. Finally, the Decision Agent synthesizes all previous evaluations (CV scores, voice transcripts, candidate metadata) into a concise report for human HR reviewers, who retain final authority over hire/reject decisions.

Rather than embedding API credentials and integration logic directly in agent code, the system abstracts external services through MCP (Model Context Protocol) servers. The Gmail MCP server exposes email capabilities like sending interview invitations and confirmations, while the Google Calendar MCP server provides calendar queries and event creation. These servers handle OAuth authentication, rate limiting, and credential management server-side, keeping secrets out of the agent codebase and enabling safe, credential-free demos. Voice operations via Twilio are managed similarly through MCP-compatible interfaces. This abstraction means agents interact with external systems through clean, standardized APIs rather than managing credentials directly, and the same MCP servers can be reused across different projects or agents.

Each agent operates on shared state objects defined using Pydantic to ensure type safety and validation. This state tracks candidate metadata (name, email, CV file path), all screening results (CV scores, voice transcripts, communication ratings), current workflow stage (applied, cv_screened, voice_done, interview_scheduled, decision_made), and tool execution history for debugging. Between agent transitions, the orchestrator updates the shared state with outputs from the previous agent, so the Voice Screening Agent receives CV scores as context, and the Decision Agent has access to all accumulated data. Critically, state is persisted to a PostgreSQL database after each milestone, enabling cognitive offloading so the active LLM context stays uncluttered and information can be retrieved when needed.

The execution flow begins when a candidate uploads a CV through the Streamlit portal. The orchestrator activates the CV Screening Agent, which parses the document and evaluates it against the job description. If the CV score passes the threshold, the orchestrator routes to the Voice Screening Agent, which makes a Twilio call, engages in dialogue, transcribes the conversation, and evaluates communication quality and technical fit. Assuming voice screening succeeds, the orchestrator activates the Meeting Scheduler Agent, which queries Google Calendar via MCP to find available HR slots, books an interview, and sends email confirmations via Gmail MCP. The orchestrator then activates the Decision Agent to prepare a comprehensive summary report. Finally, HR reviews the complete evaluation through the Gradio dashboard and makes the ultimate hire/reject/maybe decision.

Each agent binds tools to its LLM instance so it can call them during reasoning. For example, the Scheduler Agent binds calendar and email tools, allowing it to decide when to create events or send messages. When the LLM generates a tool call, the system executes the tool and returns results to the LLM for further reasoning. All outputs use Pydantic models to ensure consistent, validated formats (e.g., CVScreeningOutput with all evaluation metrics). To maintain transparency and human oversight, all reasoning traces are logged and displayed in the Gradio dashboard, showing current plan state, completed steps, pending actions, reasoning logs from each agent, tool call history with timestamps, and a complete candidate journey with scores and feedback. This visibility satisfies the hackathon's emphasis on context engineering while keeping human decision-makers informed and in control.

## ***Team***
| Member   |
| -------- |
| [Sebastian Wefers](https://github.com/Ocean-code-1995) |
| [Owen Kaplinsky](https://github.com/owenkaplinsky) |
| [SrikarMK](https://github.com/Srikarmk) |
| [Dmitri Moscoglo](https://github.com/DimiM99) |

# ***License***

This project includes and builds upon [gmail-mcp](https://github.com/theposch/gmail-mcp),  
which is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html).

This repository extends gmail-mcp for experimental integration and automation with Claude Desktop.  
All modifications are distributed under the same GPLv3 license.