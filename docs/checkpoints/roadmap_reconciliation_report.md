# Roadmap Reconciliation & Assessment Report

## 1. Reconciled Roadmap State
- **R1-13 (Governed Browser Automation)**: **IMPLEMENTED & TESTED** (Driver exists in `ophanim/browser/driver.py`, tests in `test_browser_driver.py`).
- **TASK-SKILL-1**: **ACCEPTED & CLOSED**.
- **TASK-SKILL-2**: **PAUSED**.
- **R1-14 (DB/Log Tools)**: **NOT IMPLEMENTED**.
- **R1-15 (Transaction Investigation)**: **NOT IMPLEMENTED** (Awaiting functional assistant baseline).
- **R1-16 & R1-17**: **NOT IMPLEMENTED**.

## 2. Documentation Drift Found
- `docs/progress/RELEASE-1-STATUS.md` incorrectly lists **R1-13** as `PENDING`.

## 3. Completed Tasks Incorrectly Shown as Pending
- **R1-13** (Governed Browser Automation).

## 4. Functional Component Matrix
| Component | Status |
|---|---|
| Core API | WORKING |
| Frontend/Core connectivity | BROKEN (browser mode crashes on Tauri IPC) |
| Assistant | IMPLEMENTED BUT NOT INTEGRATED (missing HTTP client, RAG logic) |
| Model provider abstraction | WORKING |
| Ollama | IMPLEMENTED |
| LM Studio | IMPLEMENTED |
| Cloud providers | IMPLEMENTED |
| Model discovery | WORKING |
| Inference | WORKING (Backend only; blocked by frontend connectivity) |
| Hybrid routing | WORKING (Completed in previous task) |
| Knowledge | PARTIAL (Ingester/Memory store exists; no API/persistence) |
| RAG | NOT IMPLEMENTED (No context injection in Chat service) |
| Citations | IMPLEMENTED BUT NOT INTEGRATED (Scoring exists, not wired) |
| Governed Browser | WORKING (Implemented, not connected to Assistant) |
| DB / Log tools | NOT IMPLEMENTED |
| Evidence | PARTIAL (Broadcaster works, not wired to tools) |
| Activity/Audit | WORKING |
| Scheduled tasks | WORKING |
| Skills | NOT IMPLEMENTED (Reframing done, execution pending) |
| Workflows | NOT IMPLEMENTED |
| Tauri/Desktop runtime | WORKING (when launched as desktop app) |

## 5. Exact Core-Unavailable Root Cause
The `useAssistantWorkspace.ts` hook tries to fetch the runtime config using `runtimeClient.getConfig()`. Because this fails fatally (due to the Tauri error below), the `catch` block fires `onError`, which sets the connection state to `'error'`. The `AppShell` component reads this non-online state and displays `"Core unavailable"`, masking the true error.

## 6. Exact Tauri/Browser-Mode Root Cause
In `apps/desktop/src/main.tsx`, the application unconditionally instantiates `new TauriAssistantRuntimeClient()`. When accessed via a standard browser (`npm run dev`), the Tauri API tries to call `window.__TAURI_IPC__`, which is undefined. This causes a `TypeError: window.__TAURI_IPC__ is not a function`. There is no environment detection to fall back to an HTTP client.

## 7. Current Assistant Execution Trace
1. **Frontend**: User types message -> `ConversationPanel.tsx` -> `useAssistantWorkspace.ts` (API Client).
2. **Runtime Boundary**: `TauriAssistantRuntimeClient.sendChat` invokes Tauri IPC command `assistant_chat`. **[FAILS IN BROWSER]**
3. **Backend API**: `ophanim.api.assistant_chat.assistant_chat` endpoint.
4. **Service**: `AssistantChatService.complete`.
5. **Router**: `ModelRouter.complete`.
6. **Provider**: `LMStudioClient` / `CloudProviderClient`.
7. **Return**: Model generated response bubbles back up.

## 8. First Broken Assistant Dependency
The lack of an **`HttpAssistantRuntimeClient`** implementation in the frontend and the absence of conditional instantiation logic in `main.tsx`.

## 9. Local Provider Status
**WORKING / IMPLEMENTED**. (LM Studio adapters exist and tests pass).

## 10. Cloud Provider Status
**WORKING / IMPLEMENTED**. (OpenAI, Gemini, Anthropic adapters exist).

## 11. Hybrid Router Status
**WORKING**. (Routing boundaries, model capabilities, and fallback tracking successfully implemented in the previous task).

## 12. Knowledge / RAG Status
**PARTIAL / NOT INTEGRATED**. `MarkdownDocumentIngester` and `InMemoryKnowledgeAdapter` exist in `adapters/knowledge.py`. However, there is no API route to upload documents, and `AssistantChatService` does not yet intercept chat messages to perform BM25 retrieval and inject context.

## 13. Governed Browser Integration Status
**IMPLEMENTED BUT NOT CONNECTED**. The Playwright driver safely exists, but the Assistant does not yet have a capability/tool mapping to invoke it.

## 14. DB / Log Tool Status
**NOT IMPLEMENTED**.

## 15. Smallest Functional Product Baseline
To reach the desired manual demonstration, we need:
1. An HTTP runtime client so the browser UI works.
2. An API route to add documents to the Knowledge Vault.
3. RAG context injection within `AssistantChatService`.

## 16. Dependency-Ordered BOOTSTRAP Backlog
- **BOOT-01 — Core/UI Connectivity**: Implement `HttpAssistantRuntimeClient` and conditional environment switching in `main.tsx`. Fix CORS if necessary.
- **BOOT-02 — Knowledge End-to-End**: Expose Knowledge Vault REST API endpoints.
- **BOOT-03 — Assistant End-to-End**: Inject Knowledge Search Results (RAG) into `ModelCompletionRequest` and display citations in the UI.

## 17. ONE Recommended Next Task
**BOOT-01 — Core/UI Connectivity**

## 18. Exact Acceptance Criteria for that Task
- The frontend detects when it is running in a browser environment (e.g., `window.__TAURI_IPC__` is undefined).
- The frontend instantiates an `HttpAssistantRuntimeClient` instead of crashing.
- The browser UI successfully fetches models from the Core API (`/api/v1/assistant/models`).
- The "Core unavailable" symptom disappears when Core is online.
- A chat message can be sent from the browser and a response received via HTTP REST.

## 19. Exact Manual Demonstration After Completion
1. Start Core backend.
2. Run `npm run dev` in `apps/desktop`.
3. Open a normal Chrome/Edge browser to `http://localhost:5173`.
4. The system reports "Core connected".
5. The model dropdown populates with local/cloud models.
6. The user types "Hello Ophanim" and receives a valid response from the model.

## 20. Files Likely Involved
- `apps/desktop/src/services/runtime.ts`
- `apps/desktop/src/main.tsx`
- `services/ophanim-core/ophanim/main.py` (Potential CORS configuration)

## 21. Risks/Blockers
- **CORS**: Since the browser runs on a different port (`5173`) than Core, FastAPI must have permissive CORS middleware for local development.
- **SSE Streams**: Browser `EventSource` requires different handling than the Tauri event listeners for the `AssistantEventStreamClient`.
