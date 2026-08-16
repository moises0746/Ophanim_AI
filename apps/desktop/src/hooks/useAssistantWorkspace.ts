import { useEffect, useMemo, useState } from 'react';
import type { AssistantEventStreamClient, EventStreamHandlers } from '../services/eventStream';
import type { AssistantRuntimeClient } from '../services/runtime';
import type {
  ActivityEventItem,
  ApprovalRequest,
  AssistantModel,
  AssistantSemanticState,
  ChatMessage,
  CitationItem,
  RoutingMode,
  ProviderStatus,
  RuntimeConnectionState,
} from '../types/events';

export interface AssistantWorkspaceState {
  assistantState: AssistantSemanticState;
  statusText: string;
  connection: RuntimeConnectionState;
  models: AssistantModel[];
  selectedModelKey: string;
  selectedModel?: AssistantModel;
  routingMode: RoutingMode;
  events: ActivityEventItem[];
  citations: CitationItem[];
  conversation: ChatMessage[];
  providerStatus: ProviderStatus | null;
  pendingApproval: ApprovalRequest | null;
  sending: boolean;
  setRoutingMode: (mode: RoutingMode) => void;
  changeModel: (modelKey: string) => void;
  sendPrompt: (text: string) => Promise<void>;
  dismissApproval: (approvalId: string) => void;
  requestStop: () => void;
}

interface UseAssistantWorkspaceOptions {
  eventStreamClient?: AssistantEventStreamClient;
  runtimeClient?: AssistantRuntimeClient;
}

export function useAssistantWorkspace({
  eventStreamClient,
  runtimeClient,
}: UseAssistantWorkspaceOptions): AssistantWorkspaceState {
  const [assistantState, setAssistantState] = useState<AssistantSemanticState>('idle');
  const [statusText, setStatusText] = useState(
    runtimeClient || eventStreamClient
      ? 'Connecting to the authorized Ophanim Core event stream.'
      : 'Browser preview: the authenticated Core runtime is not connected.',
  );
  const [connection, setConnection] = useState<RuntimeConnectionState>(
    runtimeClient || eventStreamClient ? 'connecting' : 'offline',
  );
  const [routingMode, setRoutingMode] = useState<RoutingMode>('LOCAL_ONLY');
  const [models, setModels] = useState<AssistantModel[]>([]);
  const [selectedModelKey, setSelectedModelKey] = useState('');
  const [pendingApproval, setPendingApproval] = useState<ApprovalRequest | null>(null);
  const [events, setEvents] = useState<ActivityEventItem[]>([]);
  const [citations] = useState<CitationItem[]>([]);
  const [conversation, setConversation] = useState<ChatMessage[]>([]);
  const [providerStatus, setProviderStatus] = useState<ProviderStatus | null>(null);
  const [sending, setSending] = useState(false);

  const selectedModel = useMemo(
    () => models.find((candidate) => `${candidate.provider}:${candidate.model_id}` === selectedModelKey),
    [models, selectedModelKey],
  );

  const handlers = useMemo<EventStreamHandlers>(() => ({
    onStateChange: (nextState, summary) => {
      setAssistantState(nextState);
      setStatusText(summary);
    },
    onActivityEvent: (event) => {
      setEvents((current) => {
        if (current.some((item) => item.id === event.id)) return current;
        return [event, ...current].slice(0, 200);
      });
    },
    onApprovalRequest: setPendingApproval,
    onConnectionChange: (connected) => {
      setConnection(connected ? 'online' : 'offline');
      if (connected) setStatusText('Connected. Waiting for authoritative Core state.');
    },
    onError: (error) => {
      setConnection('error');
      setStatusText(`Runtime unavailable: ${error.message}`);
    },
  }), []);

  useEffect(() => {
    if (!eventStreamClient || runtimeClient) return;
    eventStreamClient.setHandlers(handlers);
    eventStreamClient.connect();
    return () => eventStreamClient.disconnect();
  }, [eventStreamClient, handlers, runtimeClient]);

  useEffect(() => {
    if (!runtimeClient) return;
    let disposed = false;
    let disconnectEvents: (() => void) | undefined;

    void (async () => {
      try {
        setConnection('connecting');
        setStatusText('Connecting through the secure Desktop runtime.');
        const config = await runtimeClient.getConfig();
        if (!config.configured) throw new Error('local runtime is not configured');
        const configuredModels = await runtimeClient.listModels();
        const initialStatus = await runtimeClient.getProviderStatus().catch(() => null);
        if (disposed) return;
        setModels(configuredModels);
        setProviderStatus(initialStatus);
        const initial = configuredModels.find((candidate) => candidate.is_local) ?? configuredModels[0];
        if (initial) {
          setSelectedModelKey(`${initial.provider}:${initial.model_id}`);
          setRoutingMode(initial.is_local ? 'LOCAL_ONLY' : 'HYBRID_ROUTED');
        }
        disconnectEvents = await runtimeClient.connectEvents(config.workspaceId, handlers);
        if (!disposed) {
          setConnection('online');
          setStatusText(initial ? 'Connected. Ask Ophanim a question.' : 'Connected, but no model is configured.');
        }
      } catch (error) {
        if (!disposed) handlers.onError?.(error as Error);
      }
    })();

    return () => {
      disposed = true;
      disconnectEvents?.();
    };
  }, [handlers, runtimeClient]);

  const changeModel = (modelKey: string) => {
    setSelectedModelKey(modelKey);
    const nextModel = models.find(
      (candidate) => `${candidate.provider}:${candidate.model_id}` === modelKey,
    );
    if (nextModel) setRoutingMode(nextModel.is_local ? 'LOCAL_ONLY' : 'HYBRID_ROUTED');
  };

  const sendPrompt = async (text: string) => {
    if (!runtimeClient || !selectedModel || sending) {
      setStatusText('A configured Desktop runtime and model are required to send a message.');
      return;
    }
    const userMessage: ChatMessage = { role: 'user', content: text };
    const history = [...conversation, userMessage].slice(-39);
    setConversation(history);
    setSending(true);
    setStatusText('Submitting an authenticated chat request to Ophanim Core.');
    try {
      const response = await runtimeClient.sendChat({
        messages: history,
        routingMode,
        provider: selectedModel.provider,
        modelId: selectedModel.model_id,
        maxTokens: 2048,
      });
      setConversation((current) => [
        ...current,
        {
          role: 'assistant' as const,
          content: response.content,
          provider: response.provider,
          modelId: response.model_id,
          citations: response.citations,
        },
      ].slice(-40));
      setStatusText(`Response received from ${response.model_id}. Awaiting authoritative Core state.`);
    } catch (error) {
      setStatusText(`Chat request failed: ${(error as Error).message ?? String(error)}`);
    } finally {
      setSending(false);
    }
  };

  const dismissApproval = (approvalId: string) => {
    if (pendingApproval?.approvalId === approvalId) setPendingApproval(null);
    setStatusText('Approval execution is not implemented; no external action was performed.');
  };

  const requestStop = () => {
    setStatusText('Core cancellation is not implemented; no stop confirmation is claimed.');
  };

  return {
    assistantState,
    statusText,
    connection,
    models,
    selectedModelKey,
    selectedModel,
    routingMode,
    events,
    citations,
    conversation,
    providerStatus,
    pendingApproval,
    sending,
    setRoutingMode,
    changeModel,
    sendPrompt,
    dismissApproval,
    requestStop,
  };
}
