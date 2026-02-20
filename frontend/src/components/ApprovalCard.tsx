import React from 'react';
import { Approval } from '../types';
import { StatusBadge } from './StatusBadge';

interface Props {
  approval: Approval;
  onClick: (approval: Approval) => void;
}

export function ApprovalCard({ approval, onClick }: Props) {
  return (
    <div
      onClick={() => onClick(approval)}
      style={{
        background: '#fff',
        border: '1px solid #e5e7eb',
        borderRadius: 8,
        padding: '16px 20px',
        cursor: 'pointer',
        transition: 'box-shadow 0.15s',
        marginBottom: 12,
      }}
      onMouseEnter={e => (e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.10)')}
      onMouseLeave={e => (e.currentTarget.style.boxShadow = 'none')}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
        <span style={{ fontWeight: 600, fontSize: 15 }}>{approval.title}</span>
        <StatusBadge status={approval.status} />
      </div>
      <div style={{ color: '#6b7280', fontSize: 13, marginBottom: 6 }}>{approval.description}</div>
      <div style={{ fontSize: 12, color: '#9ca3af' }}>
        Requested by <strong>{approval.requestedBy}</strong> &middot;{' '}
        {new Date(approval.createdAt).toLocaleDateString()}
      </div>
    </div>
  );
}
