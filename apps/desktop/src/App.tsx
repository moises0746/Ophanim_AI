import React, { useState } from 'react';
import { OphanimVisualizer } from './components/OphanimVisualizer';
import { StatusBar } from './components/StatusBar';
import { ActivityFeed } from './components/ActivityFeed';
import { CitationDrawer } from './components/CitationDrawer';
import { ApprovalModal } from './components/ApprovalModal';
import { PromptBar } from './components/PromptBar';
import {
  ActivityEventItem,
  ApprovalRequest,
  AssistantSemanticState,
  CitationItem,
  PrivacyMode,
} from './types/events';

export const App: React.FC = () => {
  const [state, setState] = useState<AssistantSemanticState>('DORMANT');
  const [subText, setSubText] = useState<string>('Ophanim AI ready. Awaiting instruction.');
  const [privacyMode] = useState<PrivacyMode>('LOCAL_ONLY');
  const [model] = useState<string>('Llama-3-8B-Instruct (Local)');
  const [nodeConnected] = useState<boolean>(true);

  const [pendingApproval, setPendingApproval] = useState<ApprovalRequest | null>(null);

  const [events, setEvents] = useState<ActivityEventItem[]>([
    {
      id: 'evt-init-01',
      timestampUtc: new Date().toISOString(),
      type: 'assistant.state_changed',
      title: 'Control plane initialized in LOCAL_ONLY mode',
      status: 'completed',
    },
  ]);

  const [citations, setCitations] = useState<CitationItem[]>([]);

  const handlePromptSend = (text: string) => {
    // 1. Enter listening -> thinking -> executing
    setState('THINKING');
    setSubText(`Analyzing request: "${text}"`);

    const newEvt: ActivityEventItem = {
      id: `evt-${Date.now()}`,
      timestampUtc: new Date().toISOString(),
      type: 'assistant.thinking_update',
      title: `Processing: ${text}`,
      status: 'running',
    };
    setEvents((prev) => [newEvt, ...prev]);

    if (text.includes('TXN-90214') || text.includes('Investigation')) {
      setTimeout(() => {
        setState('EXECUTING');
        setSubText('Querying Diagnostic DB & Portal Runbooks...');

        setCitations([
          {
            citationId: 'cit-01',
            documentTitle: 'Payment Portal Runbook',
            uriRef: 'obsidian://vault/runbooks/payment_portal.md#ERR_TXN_TIMEOUT',
            excerpt: 'When transactions encounter a gateway timeout, verify the external gateway latency in diagnostic logs.',
            score: 0.94,
            headerPath: '### ERR_TXN_TIMEOUT',
          },
        ]);

        // Trigger human-in-the-loop approval simulation
        setTimeout(() => {
          setState('AWAITING_APPROVAL');
          setSubText('Sensitive database diagnostic query requires approval.');
          setPendingApproval({
            approvalId: 'appr-txn-1',
            taskId: 'task-investigation-01',
            toolName: 'db.query_diagnostic',
            parameters: {
              table: 'transactions',
              filter: 'order_id = "TXN-90214"',
              columns: ['id', 'status', 'error_code', 'created_at'],
            },
            riskLevel: 'medium',
            description: 'Execute parameterized read-only diagnostic query on transaction database to inspect failure reason.',
          });
        }, 1200);
      }, 800);
    } else if (text.includes('health') || text.includes('Node')) {
      setTimeout(() => {
        setState('EXECUTING');
        setSubText('Executing node diagnostic probe...');
        setTimeout(() => {
          setState('COMPLETED');
          setSubText('Device Node status: Operational. 0 errors.');
          setEvents((prev) => [
            {
              id: `evt-node-${Date.now()}`,
              timestampUtc: new Date().toISOString(),
              type: 'assistant.tool_completed',
              title: 'diagnostics.health_check executed on Device Node',
              evidenceHash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
              status: 'completed',
              durationMs: 42.5,
            },
            ...prev,
          ]);
        }, 1000);
      }, 600);
    } else {
      setTimeout(() => {
        setState('SPEAKING');
        setSubText('Ready to assist with transactions, code, and node tasks.');
        setTimeout(() => {
          setState('DORMANT');
          setSubText('Awaiting next instruction.');
        }, 1800);
      }, 1000);
    }
  };

  const handleApprove = (approvalId: string) => {
    setPendingApproval(null);
    setState('EXECUTING');
    setSubText(`Executing approved action ${approvalId}...`);

    setTimeout(() => {
      setState('COMPLETED');
      setSubText('Investigation complete: Gateway Timeout identified in upstream provider.');
      setEvents((prev) => [
        {
          id: `evt-exec-${Date.now()}`,
          timestampUtc: new Date().toISOString(),
          type: 'assistant.tool_completed',
          title: 'db.query_diagnostic completed',
          evidenceHash: '7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069',
          status: 'completed',
          durationMs: 115.0,
        },
        ...prev,
      ]);
    }, 1200);
  };

  const handleReject = (_approvalId: string) => {
    setPendingApproval(null);
    setState('BLOCKED');
    setSubText('Action rejected by operator. Investigation halted.');
  };

  const handleEmergencyStop = () => {
    setPendingApproval(null);
    setState('PAUSED');
    setSubText('EMERGENCY STOP ACTIVATED: All tasks halted immediately.');
    setEvents((prev) => [
      {
        id: `evt-stop-${Date.now()}`,
        timestampUtc: new Date().toISOString(),
        type: 'assistant.interrupted',
        title: 'Emergency stop invoked by user',
        status: 'failed',
      },
      ...prev,
    ]);
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

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 340px',
        gap: '20px',
        flex: 1,
        minHeight: '600px'
      }}>
        {/* Main Orchestration & Presence Area */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="glass-panel" style={{ flex: '0 0 auto', padding: '16px' }}>
            <OphanimVisualizer state={state} subText={subText} />
          </div>

          <div style={{ flex: 1, minHeight: '260px' }}>
            <ActivityFeed events={events} />
          </div>

          <PromptBar onSend={handlePromptSend} disabled={state === 'AWAITING_APPROVAL'} />
        </div>

        {/* Knowledge & Citations Sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <CitationDrawer citations={citations} />
        </div>
      </div>

      <ApprovalModal
        request={pendingApproval}
        onApprove={handleApprove}
        onReject={handleReject}
      />
    </div>
  );
};

export default App;
