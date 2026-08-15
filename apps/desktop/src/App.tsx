import React, { useEffect, useState } from 'react';
import { ActivityFeed } from './components/ActivityFeed';
import { ApprovalModal } from './components/ApprovalModal';
import { CitationDrawer } from './components/CitationDrawer';
import { OphanimVisualizer } from './components/OphanimVisualizer';
import { PromptBar } from './components/PromptBar';
import { StatusBar } from './components/StatusBar';
import { AssistantEventStreamClient } from './services/eventStream';
import {
  ActivityEventItem,
  ApprovalRequest,
  AssistantSemanticState,
  CitationItem,
  PrivacyMode,
} from './types/events';

interface AppProps {
  eventStreamClient?: AssistantEventStreamClient;
}

export const App: React.FC<AppProps> = ({ eventStreamClient }) => {
  const [state, setState] = useState<AssistantSemanticState>('OFFLINE');
  const [subText, setSubText] = useState('No authorized Core event stream is configured.');
  const [privacyMode] = useState<PrivacyMode>('LOCAL_ONLY');
  const [model] = useState('Llama-3-8B-Instruct (Local)');
  const [nodeConnected, setNodeConnected] = useState(false);
  const [pendingApproval, setPendingApproval] = useState<ApprovalRequest | null>(null);
  const [events, setEvents] = useState<ActivityEventItem[]>([]);
  const [citations] = useState<CitationItem[]>([]);

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

  const handlePromptSend = (_text: string) => {
    setSubText('Task submission is not part of R1-12; no task was created.');
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

          <div style={{ flex: 1, minHeight: '260px' }}>
            <ActivityFeed events={events} />
          </div>

          <PromptBar onSend={handlePromptSend} disabled={state === 'AWAITING_APPROVAL'} />
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
