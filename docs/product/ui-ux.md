# Ophanim AI UI/UX Specification

## UX Goal

Ophanim should communicate three things at all times: what it understands, what it is doing, and whether the user must act.

## Primary Desktop Layout

```text
+--------------------------------------------------------------------------------+
| Ophanim AI | Workspace | Privacy Mode | Model | Browser | Notifications         |
+----------------------+--------------------------------------+------------------+
| Agent Mesh           | Animated Ophanim Assistant          | Task / Evidence  |
|                      |                                      |                  |
| Knowledge   READY    |              [Avatar]                | Goal             |
| Browser     WORKING  |                                      | Current step     |
| Operations  READY    |           "Investigating..."        | Evidence         |
| Developer   READY    |                                      | Sources          |
| Research    READY    | Listening / Thinking / Browsing      | Approval         |
|                      |                                      |                  |
+----------------------+--------------------------------------+------------------+
| Conversation / Transcript / Suggested Response / Command Composer               |
+--------------------------------------------------------------------------------+
```

## Assistant States

- Idle
- Listening
- Transcribing
- Thinking
- Retrieving Knowledge
- Browsing
- Investigating
- Waiting for Approval
- Speaking
- Complete
- Warning
- Error
- Offline/Private

The animated Ophanim visual should be implemented with a state machine (Rive is the preferred first evaluation). The animation reflects application state; it does not receive arbitrary animation instructions from the model.

## Agent Mesh

Each agent card shows:

- name
- capability icon
- current state
- current task summary
- elapsed time
- evidence count
- approval indicator

Selecting an agent opens its activity panel with tool calls, evidence, screenshots, source links, and sanitized status information. Do not expose hidden chain-of-thought.

## Native Browser UX

Ophanim Browser should support a split view:

```text
+---------------------------------------------+------------------------------+
| Browser                                     | Ophanim Browser Agent        |
| URL / navigation                            | Objective                    |
|                                             | Current action               |
| Approved web application                    | Extracted evidence           |
|                                             | Planned next step            |
|                                             | [Approve] [Stop] [Evidence] |
+---------------------------------------------+------------------------------+
```

A visible boundary must distinguish READ actions from state-changing actions. Approval dialogs state exactly what will happen, in which application/environment, and what data is affected.

## Voice UX

Modes:

- Push-to-Talk: default MVP voice mode
- Silent/Overlay: text response only
- Headset: optional private TTS
- Assistant: voice + animation
- Meeting Coach: detect questions to the owner and privately suggest responses
- Privacy: local providers only

Controls must always expose microphone state and a global mute/pause action.

## Visual Direction

- dark enterprise console, not a game HUD
- Ophanim-inspired concentric/ring motif used sparingly as the assistant identity
- high information density with calm hierarchy
- clear green/amber/red only for semantic state, not decoration
- evidence and approvals take priority over decorative analytics
- responsive desktop-first layout

## Accessibility

- keyboard navigation
- screen-reader labels
- reduced-motion mode for the animated assistant
- high-contrast support
- captions/transcripts for all voice interactions
- no critical status encoded by color alone
