# ADR 018: Extensible Skill Architecture

**Status:** Accepted
**Date:** 2026-08-16
**Deciders:** Ophanim AI Architecture Team

## Context and Problem Statement

Ophanim AI's early documentation and product positioning heavily emphasized its role as an "AI Transaction Investigation Agent." While the Python backend (`ophanim-core`) was implemented with abstract generic concepts (Tasks, Agents, Policies, Orchestrators), the product scope, test fixtures, and desktop UI simulation tightly coupled the platform's primary purpose to transaction investigation. 

This coupling creates several issues:
1. It artificially restricts Ophanim's potential as a generic AI Coworker platform.
2. It misleads developers into hard-coding transaction-specific logic into Core (e.g., expecting a `reference_number` input inherently, or hardcoding the portal-db-log investigation workflow in the orchestrator).
3. It makes it difficult to add new capabilities (e.g., Kubernetes Troubleshooting, Log Analysis) without creating entirely new monolithic agents or polluting the core domain.

## Decision

We will reframe the "AI Transaction Investigation Agent" into a "Transaction Investigation Skill". 

Ophanim AI will formally adopt an **Extensible Skill Architecture** where:
*   **Ophanim Core** is a generic orchestration platform responsible for managing Task lifecycles, evaluating Policies, and executing generic Tool capabilities safely.
*   **Skills** are installable, configurable capability packages containing a specific workflow, required inputs/outputs, and capability dependencies.
*   "Transaction Investigation" becomes the first canonical *Skill* hosted by Ophanim, rather than the singular purpose of the product.

### Skill Domain Model
The `ophanim.domain.skills` layer will introduce:
- `SkillDefinition`: Metadata about a skill (ID, Name, Version).
- `SkillManifest`: A technology-neutral contract (serializable to YAML/JSON) defining inputs, outputs, required capabilities, and policies.
- `SkillRegistry`: An abstract interface to register, list, and validate skills against available system tools/capabilities. 
- `SkillWorkflow`: An abstract definition of the agent's execution path.

### Security and Execution
A Skill does NOT grant authority. When a skill is executed:
1. The orchestration layer resolves its required capabilities.
2. The Policy Engine evaluates if the tenant/user is authorized for those capabilities.
3. The deterministic Tool boundaries still intercept and govern (e.g. enforce `read-only`) every side-effect.

## Consequences

### Positive
- **Extensibility**: It becomes trivial to add new skills (e.g., Incident Responder, Content Creator) without modifying Ophanim Core.
- **Clean Boundaries**: Transaction-specific assumptions (like checking a specific portal URL) stay within the Skill Manifest, keeping the orchestrator pure.
- **Product Growth**: The Desktop Assistant can now offer a "Skills Dashboard" for users to discover and configure capabilities.

### Negative / Risks
- **Overhead**: Introduces a new layer of abstraction (Skill Registry) that must be populated and maintained.
- **UI Refactoring**: The desktop application (`App.tsx`) will need to be abstracted to dynamically render execution forms based on `SkillManifest.inputs` rather than hardcoding the transaction investigation UI.
