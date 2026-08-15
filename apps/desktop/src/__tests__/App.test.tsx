import { describe, it, expect } from 'vitest';
import { renderToString } from 'react-dom/server';
import { OphanimVisualizer } from '../components/OphanimVisualizer';
import { StatusBar } from '../components/StatusBar';
import { ActivityFeed } from '../components/ActivityFeed';
import { CitationDrawer } from '../components/CitationDrawer';
import { ApprovalModal } from '../components/ApprovalModal';

describe('Desktop Assistant Components', () => {
  it('renders OphanimVisualizer with 12 semantic states', () => {
    const states = [
      'OFFLINE',
      'INITIALIZING',
      'DORMANT',
      'LISTENING',
      'THINKING',
      'SPEAKING',
      'EXECUTING',
      'AWAITING_APPROVAL',
      'BLOCKED',
      'PAUSED',
      'ERROR',
      'COMPLETED',
    ] as const;

    for (const st of states) {
      const html = renderToString(<OphanimVisualizer state={st} subText="State test" />);
      expect(html).toContain(`state-${st}`);
      expect(html).toContain(st.replace('_', ' '));
    }
  });

  it('renders StatusBar with model, mode, and emergency stop button', () => {
    const html = renderToString(
      <StatusBar
        state="DORMANT"
        model="Llama-3-8B"
        privacyMode="LOCAL_ONLY"
        nodeConnected={true}
        onEmergencyStop={() => {}}
      />
    );
    expect(html).toContain('OPHANIM');
    expect(html).toContain('Llama-3-8B');
    expect(html).toContain('LOCAL_ONLY');
    expect(html).toContain('STOP');
  });

  it('renders ActivityFeed with evidence receipts', () => {
    const html = renderToString(
      <ActivityFeed
        events={[
          {
            id: 'evt-1',
            timestampUtc: '2026-08-15T12:00:00Z',
            type: 'assistant.tool_completed',
            title: 'Diagnostic DB Query',
            evidenceHash: 'abc123sha256hash',
            status: 'completed',
          },
        ]}
      />
    );
    expect(html).toContain('Diagnostic DB Query');
    expect(html).toContain('abc123sha256hash');
  });

  it('renders CitationDrawer with scores and references', () => {
    const html = renderToString(
      <CitationDrawer
        citations={[
          {
            citationId: 'cit-1',
            documentTitle: 'Runbook Guide',
            uriRef: 'obsidian://vault/runbook.md',
            excerpt: 'Timeout error handling guide.',
            score: 0.95,
            headerPath: '### ERR_TIMEOUT',
          },
        ]}
      />
    );
    expect(html).toContain('Runbook Guide');
    expect(html).toContain('0.95');
    expect(html).toContain('Timeout error handling guide.');
  });

  it('renders ApprovalModal when request is active', () => {
    const html = renderToString(
      <ApprovalModal
        request={{
          approvalId: 'appr-1',
          taskId: 'task-1',
          toolName: 'db.query',
          parameters: { table: 'txns' },
          riskLevel: 'medium',
          description: 'Approval required for sensitive database query.',
        }}
        onApprove={() => {}}
        onReject={() => {}}
      />
    );
    expect(html).toContain('Human Approval Required');
    expect(html).toContain('db.query');
    expect(html).toContain('Approve &amp; Execute');
  });
});
