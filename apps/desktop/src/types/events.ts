export type AssistantSemanticState =
  | 'OFFLINE'
  | 'INITIALIZING'
  | 'DORMANT'
  | 'LISTENING'
  | 'THINKING'
  | 'SPEAKING'
  | 'EXECUTING'
  | 'AWAITING_APPROVAL'
  | 'BLOCKED'
  | 'PAUSED'
  | 'ERROR'
  | 'COMPLETED';

export type CoreAssistantSemanticState =
  | 'idle'
  | 'listening'
  | 'understanding'
  | 'planning'
  | 'delegating'
  | 'working'
  | 'waiting_for_tool'
  | 'waiting_for_approval'
  | 'speaking'
  | 'completed'
  | 'blocked'
  | 'error';

export type AssistantEventType =
  | 'assistant.state.changed'
  | 'agent.assigned'
  | 'agent.started'
  | 'agent.progressed'
  | 'agent.blocked'
  | 'agent.failed'
  | 'agent.completed'
  | 'capability.requested'
  | 'policy.evaluated'
  | 'tool.requested'
  | 'tool.denied'
  | 'tool.started'
  | 'tool.progressed'
  | 'tool.completed'
  | 'tool.failed'
  | 'tool.cancelled'
  | 'evidence.captured'
  | 'evidence.verified'
  | 'approval.requested'
  | 'approval.granted'
  | 'approval.denied'
  | 'approval.expired'
  | 'task.created'
  | 'task.planning_started'
  | 'task.work_started'
  | 'task.blocked'
  | 'task.cancellation_requested'
  | 'task.cancelled'
  | 'task.failed'
  | 'task.completed'
  | 'voice.listening_started'
  | 'voice.listening_stopped'
  | 'voice.transcription_started'
  | 'voice.transcription_completed'
  | 'voice.speech_started'
  | 'voice.speech_completed'
  | 'voice.speech_interrupted'
  | 'voice.microphone_muted';

export type PrivacyMode = 'LOCAL_ONLY' | 'PRIVATE' | 'CLOUD_ASSISTED';

export interface ApprovalRequest {
  approvalId: string;
  taskId: string;
  toolName: string;
  parameters: Record<string, unknown>;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  description: string;
}

export interface CitationItem {
  citationId: string;
  documentTitle: string;
  uriRef: string;
  excerpt: string;
  score: number;
  headerPath: string;
}

export interface ActivityEventItem {
  id: string;
  timestampUtc: string;
  type: AssistantEventType;
  title: string;
  details?: Record<string, unknown>;
  evidenceHash?: string;
  status: 'running' | 'completed' | 'failed' | 'approval_required';
  durationMs?: number;
}

export interface EventEnvelope {
  event_id: string;
  event_type: AssistantEventType;
  event_schema_version: string;
  occurred_at: string;
  emitted_at: string;
  producer: string;
  correlation_id: string;
  workspace_id: string;
  environment: string;
  data_scope: string;
  visibility_classification: string;
  display_summary: string;
  payload: Record<string, unknown>;
  task_id?: string | null;
  task_step_id?: string | null;
  agent_profile_id?: string | null;
  agent_profile_version?: string | null;
  tool_call_id?: string | null;
  policy_decision_id?: string | null;
  approval_id?: string | null;
  sequence?: number | null;
  evidence_refs: string[];
  artifact_refs: string[];
}
