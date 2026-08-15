import React from 'react';
import { ApprovalRequest } from '../types/events';

interface ApprovalModalProps {
  request: ApprovalRequest | null;
  onApprove: (approvalId: string) => void;
  onReject: (approvalId: string) => void;
}

export const ApprovalModal: React.FC<ApprovalModalProps> = ({ request, onApprove, onReject }) => {
  if (!request) return null;

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(6, 8, 20, 0.85)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px',
    }}>
      <div className="glass-panel" style={{
        maxWidth: '520px',
        width: '100%',
        padding: '24px',
        border: '1px solid rgba(245, 158, 11, 0.5)',
        boxShadow: '0 0 30px rgba(245, 158, 11, 0.2)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '8px',
            background: 'rgba(245, 158, 11, 0.2)',
            color: 'var(--accent-amber)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 700,
          }}>
            !
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Human Approval Required
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--accent-amber)', textTransform: 'uppercase', fontWeight: 600 }}>
              Risk Level: {request.riskLevel}
            </span>
          </div>
        </div>

        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '16px', lineHeight: 1.5 }}>
          {request.description}
        </p>

        <div style={{
          background: 'rgba(0, 0, 0, 0.3)',
          padding: '12px',
          borderRadius: '8px',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.8rem',
          color: '#cbd5e1',
          marginBottom: '20px',
          maxHeight: '140px',
          overflowY: 'auto'
        }}>
          <div><strong>Tool:</strong> {request.toolName}</div>
          <pre style={{ marginTop: '6px', whiteSpace: 'pre-wrap' }}>
            {JSON.stringify(request.parameters, null, 2)}
          </pre>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button
            onClick={() => onReject(request.approvalId)}
            style={{
              padding: '8px 16px',
              borderRadius: '8px',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              background: 'transparent',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.85rem'
            }}
          >
            Reject Action
          </button>
          <button
            onClick={() => onApprove(request.approvalId)}
            style={{
              padding: '8px 18px',
              borderRadius: '8px',
              border: 'none',
              background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
              color: '#000000',
              cursor: 'pointer',
              fontWeight: 700,
              fontSize: '0.85rem',
              boxShadow: '0 0 16px rgba(245, 158, 11, 0.4)'
            }}
          >
            Approve & Execute
          </button>
        </div>
      </div>
    </div>
  );
};
