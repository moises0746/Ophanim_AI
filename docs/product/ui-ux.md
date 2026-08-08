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

The animation is a functional status surface, not decoration.

Suggested visual identity: concentric Ophanim-inspired rings/core with restrained enterprise motion.

State mapping:

- IDLE — slow subtle motion;
- LISTENING — audio-reactive pulse;
- TRANSCRIBING — focused inner-ring motion;
- THINKING — reasoning pulse/rotation;
- DELEGATING — connections illuminate from center to agents;
- ORCHESTRATING — multiple active agent connections;
- RETRIEVING — Knowledge node/ring active;
- BROWSING — Browser node/ring active;
- INVESTIGATING — evidence/correlation motion;
- WAITING_FOR_APPROVAL — clear amber/static state;
- SPEAKING — TTS waveform/core response;
- COMPLETE — brief convergence/confirmation;
- WARNING/ERROR — calm semantic warning, no dramatic flashing.

Evaluate Rive first because deterministic state machines map well to AssistantState events. Lottie is acceptable for simpler non-interactive effects.

Reduced-motion mode is required.

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

Every row comes from sanitized backend events.

## Voice UX

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
