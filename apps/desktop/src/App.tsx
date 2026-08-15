import React, { useEffect, useState } from 'react';
import { ActivityFeed } from './components/ActivityFeed';
import { ApprovalModal } from './components/ApprovalModal';
import { CitationDrawer } from './components/CitationDrawer';
import { ConversationPanel } from './components/ConversationPanel';
import { OphanimVisualizer } from './components/OphanimVisualizer';
import { PromptBar } from './components/PromptBar';
import { StatusBar } from './components/StatusBar';
import { AssistantEventStreamClient } from './services/eventStream';
import { AssistantRuntimeClient } from './services/runtime';
import {
  ActivityEventItem,
  ApprovalRequest,
  AssistantModel,
  AssistantSemanticState,
  ChatMessage,
  CitationItem,
  PrivacyMode,
} from './types/events';

interface AppProps {
  eventStreamClient?: AssistantEventStreamClient;
  runtimeClient?: AssistantRuntimeClient;
}

export const App: React.FC<AppProps> = ({ eventStreamClient, runtimeClient }) => {
  const [state, setState] = useState<AssistantSemanticState>('OFFLINE');
  const [subText, setSubText] = useState('No authorized Core event stream is configured.');
  const [privacyMode, setPrivacyMode] = useState<PrivacyMode>('LOCAL_ONLY');
  const [models, setModels] = useState<AssistantModel[]>([]);
  const [selectedModelKey, setSelectedModelKey] = useState('');
  const [nodeConnected, setNodeConnected] = useState(false);
  const [pendingApproval, setPendingApproval] = useState<ApprovalRequest | null>(null);
  const [events, setEvents] = useState<ActivityEventItem[]>([]);
  const [citations] = useState<CitationItem[]>([]);
  const [conversation, setConversation] = useState<ChatMessage[]>([]);
  const [sending, setSending] = useState(false);

  const selectedModel = models.find(
    (candidate) => `${candidate.provider}:${candidate.model_id}` === selectedModelKey,
  );
  const model = selectedModel?.display_name ?? 'No model configured';

  useEffect(() => {
    if (!eventStreamClient) return;

    setState('INITIALIZING');
    setSubText('Connecting to the authorized Ophanim Core event stream...');
    eventStreamClient.setHandlers({
      onStateChange: (nextState, summary) => {
        setState(nextState);
        setSubText(summary);
      },
      onActivityEvent: (event) => {
        setEvents((current) => {
          if (current.some((item) => item.id === event.id)) return current;
          return [event, ...current].slice(0, 200);
        });
      },
      onApprovalRequest: setPendingApproval,
      onConnectionChange: (connected) => {
        setNodeConnected(connected);
        if (connected) setSubText('Connected. Waiting for authoritative Core state.');
      },
      onError: (error) => {
        setNodeConnected(false);
        setState('OFFLINE');
        setSubText(`Event delivery unavailable: ${error.message}`);
      },
    });
    eventStreamClient.connect();
    return () => eventStreamClient.disconnect();
  }, [eventStreamClient]);

  useEffect(() => {
    if (!runtimeClient) return;
    let disposed = false;
    let disconnectEvents: (() => void) | undefined;
    const handlers = {
      onStateChange: (nextState: AssistantSemanticState, summary: string) => {
        if (!disposed) {
          setState(nextState);
          setSubText(summary);
        }
      },
      onActivityEvent: (event: ActivityEventItem) => {
        if (!disposed) {
          setEvents((current) => {
            if (current.some((item) => item.id === event.id)) return current;
            return [event, ...current].slice(0, 200);
          });
        }
      },
      onApprovalRequest: (request: ApprovalRequest) => {
        if (!disposed) setPendingApproval(request);
      },
      onConnectionChange: (connected: boolean) => {
        if (!disposed) setNodeConnected(connected);
      },
      onError: (error: Error) => {
        if (!disposed) {
          setNodeConnected(false);
          setState('OFFLINE');
          setSubText(`Runtime unavailable: ${error.message}`);
        }
      },
    };

    void (async () => {
      try {
        setState('INITIALIZING');
        setSubText('Connecting through the secure Desktop runtime...');
        const config = await runtimeClient.getConfig();
        if (!config.configured) throw new Error('local runtime is not configured');
        const configuredModels = await runtimeClient.listModels();
        if (disposed) return;
        setModels(configuredModels);
        const initial = configuredModels.find((candidate) => candidate.is_local) ?? configuredModels[0];
        if (initial) {
          setSelectedModelKey(`${initial.provider}:${initial.model_id}`);
          setPrivacyMode(initial.is_local ? 'LOCAL_ONLY' : 'CLOUD_ASSISTED');
        }
        disconnectEvents = await runtimeClient.connectEvents(config.workspaceId, handlers);
        if (!disposed) {
          setState('DORMANT');
          setSubText(
            initial
              ? 'Connected. Ask Ophanim a question.'
              : 'Connected, but no model is configured.',
          );
        }
      } catch (error) {
        handlers.onError(error as Error);
      }
    })();

    return () => {
      disposed = true;
      disconnectEvents?.();
    };
  }, [runtimeClient]);

  const handlePromptSend = async (text: string) => {
    if (!runtimeClient || !selectedModel || sending) {
      setSubText('No configured Desktop runtime and model are available.');
      return;
    }
    const userMessage: ChatMessage = { role: 'user', content: text };
    const history = [...conversation, userMessage].slice(-39);
    setConversation(history);
    setSending(true);
    setState('THINKING');
    setSubText('Submitting an authenticated chat request to Ophanim Core...');
    try {
      const response = await runtimeClient.sendChat({
        messages: history,
        privacyMode,
        provider: selectedModel.provider,
        modelId: selectedModel.model_id,
        maxTokens: 2048,
      });
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.content,
      };
      setConversation((current) => [...current, assistantMessage].slice(-40));
      setSubText(`Response completed by ${response.model_id}.`);
      setState('COMPLETED');
    } catch (error) {
      setState('ERROR');
      setSubText(`Chat failed: ${(error as Error).message ?? String(error)}`);
    } finally {
      setSending(false);
    }
  };

  const handleModelChange = (modelKey: string) => {
    setSelectedModelKey(modelKey);
    const nextModel = models.find(
      (candidate) => `${candidate.provider}:${candidate.model_id}` === modelKey,
    );
    if (nextModel) setPrivacyMode(nextModel.is_local ? 'LOCAL_ONLY' : 'CLOUD_ASSISTED');
  };

  const handleApprovalAction = (_approvalId: string) => {
    setPendingApproval(null);
    setSubText('Approval execution is not part of R1-12; no action was performed.');
  };

  const handleEmergencyStop = () => {
    setSubText('Core cancellation is not wired in R1-12; no stop confirmation is claimed.');
  };

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '20px', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <StatusBar
        state={state}
        model={model}
        privacyMode={privacyMode}
        nodeConnected={nodeConnected}
        onEmergencyStop={handleEmergencyStop}
      />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '20px', flex: 1, minHeight: '600px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="glass-panel" style={{ flex: '0 0 auto', padding: '16px' }}>
            <OphanimVisualizer state={state} subText={subText} />
          </div>

          <ConversationPanel messages={conversation} />

          <div style={{ flex: 1, minHeight: '260px' }}>
            <ActivityFeed events={events} />
          </div>

          <PromptBar
            onSend={(text) => void handlePromptSend(text)}
            disabled={
              state === 'AWAITING_APPROVAL' ||
              sending ||
              !runtimeClient ||
              !selectedModel
            }
            models={models}
            selectedModelKey={selectedModelKey}
            privacyMode={privacyMode}
            onModelChange={handleModelChange}
            onPrivacyChange={setPrivacyMode}
          />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <CitationDrawer citations={citations} />
        </div>
      </div>

      <ApprovalModal
        request={pendingApproval}
        onApprove={handleApprovalAction}
        onReject={handleApprovalAction}
      />
    </div>
  );
};

export default App;
