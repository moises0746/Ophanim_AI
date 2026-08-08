# Ophanim AI UI/UX Specification

## Product Hierarchy

The first/default page is **Ophanim Assistant**. Dashboard/analytics is secondary.

Primary navigation:

```text
Assistant          <- default route
Tasks
Agents
Browser
Knowledge
Workflows
Integrations
Activity
Dashboard
Settings
```

## Assistant Home

```text
+--------------------------------------------------------------------------------+
| OPHANIM AI | Workspace | Privacy | Model | Browser | Notifications | Profile     |
+----------------------+--------------------------------------+------------------+
| Agent Mesh           | Animated Ophanim Assistant          | Live Activity    |
|                      |                                      |                  |
| Browser      WORKING |                [O]                   | Current task     |
| Knowledge    WORKING |                                      | Current step     |
| Operations   READY   |          "Investigating..."         | Evidence count   |
| Developer    READY   |                                      | Sources          |
| Research     READY   | Listen/Think/Delegate/Browse/Speak   | Approvals        |
| Content      READY   |                                      |                  |
+----------------------+--------------------------------------+------------------+
| Conversation / Transcript / Suggested Response / Command Composer               |
| > Ask Ophanim or hold Push-to-Talk...                                            |
+--------------------------------------------------------------------------------+
```

The screen must answer:

1. What is Ophanim doing?
2. Which agents are active?
3. What evidence has been collected?
4. Does the user need to approve/act?
5. What is the result?

## Animated Ophanim

The Ophanim visual on the Home/Assistant surface is a functional, state-driven status surface, not decoration and not a static logo. Its state must be derived from authoritative Assistant and Agent activity emitted by Ophanim Core; arbitrary UI timers must never invent task, agent, tool, approval, completion, blocked, or error state.

Suggested visual identity: concentric Ophanim-inspired rings/core with restrained enterprise motion.

State mapping:

The single canonical state model is defined in [Assistant State Projection](../assistant/assistant-state-projection.md). The detailed visual terms below are activity details mapped into those states, not competing top-level states. Events come from [Assistant Event Contracts](../assistant/assistant-event-contracts.md).

Use the canonical semantic states and detail mappings in [Assistant State Projection](../assistant/assistant-state-projection.md). Specialized activity (transcription, retrieval, browsing, investigation, orchestration, and warnings) must not become a second top-level state model.

Evaluate Rive first because deterministic state machines map well to AssistantState events. Lottie is acceptable for simpler non-interactive effects.

Reduced-motion mode is required.

### Reserved Semantic Presentation States

The UI architecture must eventually support:

- `idle` - ready, with restrained ambient motion;
- `listening` - microphone capture with an accessible listening indicator;
- `understanding` - interpreting or transcribing user input;
- `planning` - preparing the task plan;
- `delegating` - connecting work to one or more bounded agents;
- `working` - active orchestration, retrieval, browsing, investigation, or other governed work;
- `waiting_for_tool` - paused on an authoritative tool lifecycle event;
- `waiting_for_approval` - clearly indicates that user approval is required;
- `speaking` - real playback/audio-reactive output, not a simulated timer;
- `completed` - verified completion;
- `blocked` - unable to proceed without a dependency, decision, authorization, or safe recovery;
- `error` - a terminal or actionable failure.

The later Assistant event-contract task must define the canonical event-to-presentation mapping and reconcile these semantic UI states with the current event-model vocabulary. This document does not define or implement that transport or contract.

The future visualization architecture must reserve support for:

- microphone/listening visualization;
- real audio-reactive speaking visualization;
- active-agent connection animation;
- tool/activity visualization;
- task progress;
- approval-required state;
- interruption and stop control;
- accessibility and reduced-motion mode;
- a text fallback for every visual state.

Reduced-motion mode must preserve every semantic distinction without depending on motion. Color alone is insufficient; text, icons, and assistive-technology labels must communicate the same state.

Animation, microphone/audio processing, voice playback, WebSocket/SSE transport, Assistant events, frontend state management, and the desktop runtime are not implemented by S00-T02. They are deferred to the appropriate Assistant/event-contract and desktop UI Sprints.

## Agent Mesh

Agent cards/nodes show:

- agent name/capability;
- lifecycle state;
- current task summary;
- elapsed time;
- evidence count;
- approval indicator;
- failure/blocked indicator.

Selecting an agent opens activity/evidence, not hidden model chain-of-thought.

Initial visible agents:

- Knowledge Agent;
- Browser Agent;
- Operations Agent;
- Developer Agent;
- Research Agent;
- Communication Agent;
- Content Agent.

## Live Activity

Example:

```text
00:01  Ophanim            Created investigation task
00:02  Browser Agent      Opening approved transaction portal
00:04  Knowledge Agent    Searching runbook
00:05  Operations Agent   Searching approved logs
00:08  Browser Agent      Captured transaction evidence
00:11  Ophanim            Correlating evidence
```

Every row must correspond to a real, sanitized, auditable activity event emitted by Ophanim Core. The UI may format or group events for readability, but must not fabricate work, tool use, evidence, approvals, or completion through local timers or decorative animation.

## Voice UX

In this section, voice MVP means the later Assistant voice increment. Push-to-talk, voice recognition, VAD, STT, TTS, wake word, and always-on microphone processing are not required for the first transaction-investigation backend slice, which must remain fully operable through text.

Modes:

- Push-to-Talk — default MVP;
- Silent/Overlay — text only;
- Headset — private TTS;
- Assistant — voice + animation;
- Meeting Coach — later question/addressee detection;
- Private — local providers only.

Microphone state and global mute/pause must always be visible.

## Browser UX

```text
+--------------------------------------------------+-----------------------------+
| Ophanim Browser                                  | Browser Agent               |
| URL/navigation                                   | Objective                   |
|                                                  | Current action              |
| Approved application                             | Extracted evidence          |
|                                                  | Proposed next action        |
|                                                  | [Stop] [Evidence] [Approve]|
+--------------------------------------------------+-----------------------------+
```

Read versus state-changing actions must be visually distinct.

## Dashboard

Dashboard is an operational/system page for:

- active tasks/agents;
- model/runtime health;
- system resource usage;
- tool/MCP/browser status;
- success/failure metrics;
- audit/evidence counts;
- queue/latency health.

Avoid decorative/fake "AI prediction" charts. Every widget must be actionable or operationally meaningful.

## Design Direction

- dark enterprise console;
- modern but restrained;
- high information density with clear hierarchy;
- violet/blue Ophanim brand accents;
- green/amber/red reserved for semantic state;
- avoid game-like HUD clutter;
- evidence, approvals and current task outrank analytics.

## Accessibility

- keyboard navigation;
- screen-reader labels;
- captions/transcripts for voice;
- reduced motion;
- high contrast;
- status not encoded only by color;
- focus visibility;
- scalable text/layout.
