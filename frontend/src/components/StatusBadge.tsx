import React from 'react';
import { ApprovalStatus } from '../types';

const styles: Record<ApprovalStatus, React.CSSProperties> = {
  pending:  { background: '#fef3c7', color: '#92400e', border: '1px solid #fcd34d' },
  approved: { background: '#d1fae5', color: '#065f46', border: '1px solid #6ee7b7' },
  rejected: { background: '#fee2e2', color: '#991b1b', border: '1px solid #fca5a5' },
};

interface Props {
  status: ApprovalStatus;
}

export function StatusBadge({ status }: Props) {
  return (
    <span style={{
      ...styles[status],
      padding: '2px 10px',
      borderRadius: 12,
      fontSize: 12,
      fontWeight: 600,
      textTransform: 'capitalize',
      display: 'inline-block',
    }}>
      {status}
    </span>
  );
}
