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

export type AssistantEventType =
  | 'assistant.state_changed'
  | 'assistant.listening_update'
  | 'assistant.thinking_update'
  | 'assistant.speaking_chunk'
  | 'assistant.action_proposed'
  | 'assistant.approval_requested'
  | 'assistant.tool_started'
  | 'assistant.tool_progress'
  | 'assistant.tool_completed'
  | 'assistant.tool_failed'
  | 'assistant.evidence_produced'
  | 'assistant.interrupted';

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
