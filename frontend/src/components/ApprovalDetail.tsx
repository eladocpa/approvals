import React, { useState } from 'react';
import { Approval, ApprovalStatus } from '../types';
import { StatusBadge } from './StatusBadge';

interface Props {
  approval: Approval;
  onUpdateStatus: (id: string, status: ApprovalStatus, comment?: string, author?: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onBack: () => void;
}

export function ApprovalDetail({ approval, onUpdateStatus, onDelete, onBack }: Props) {
  const [comment, setComment] = useState('');
  const [author, setAuthor] = useState('');
  const [loading, setLoading] = useState(false);

  const handleStatus = async (status: ApprovalStatus) => {
    setLoading(true);
    await onUpdateStatus(approval.id, status, comment.trim() || undefined, author.trim() || undefined);
    setComment('');
    setLoading(false);
  };

  const handleDelete = async () => {
    if (!window.confirm('Delete this approval request?')) return;
    await onDelete(approval.id);
  };

  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '7px 11px', border: '1px solid #d1d5db', borderRadius: 6, fontSize: 13,
  };

  const btnStyle = (color: string, text: string): React.CSSProperties => ({
    background: color, color: text, border: 'none', borderRadius: 6, padding: '7px 16px',
    fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1, fontSize: 13,
  });

  return (
    <div>
      <button onClick={onBack} style={{ background: 'none', border: 'none', color: '#2563eb', cursor: 'pointer', fontWeight: 600, marginBottom: 16, fontSize: 14 }}>
        &larr; Back to list
      </button>
      <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <h2 style={{ fontSize: 18, fontWeight: 700 }}>{approval.title}</h2>
          <StatusBadge status={approval.status} />
        </div>
        <p style={{ color: '#374151', marginBottom: 16 }}>{approval.description}</p>
        <div style={{ fontSize: 13, color: '#6b7280', marginBottom: 20 }}>
          <span>Requested by <strong>{approval.requestedBy}</strong></span>
          <span style={{ margin: '0 8px' }}>&middot;</span>
          <span>Created {new Date(approval.createdAt).toLocaleString()}</span>
          <span style={{ margin: '0 8px' }}>&middot;</span>
          <span>Updated {new Date(approval.updatedAt).toLocaleString()}</span>
        </div>

        {/* Comments */}
        {approval.comments.length > 0 && (
          <div style={{ marginBottom: 20 }}>
            <h4 style={{ fontSize: 13, fontWeight: 700, color: '#374151', marginBottom: 8 }}>Comments</h4>
            {approval.comments.map(c => (
              <div key={c.id} style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 6, padding: '8px 12px', marginBottom: 6 }}>
                <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 2 }}>
                  <strong>{c.author}</strong> &middot; {new Date(c.createdAt).toLocaleString()}
                </div>
                <div style={{ fontSize: 13 }}>{c.text}</div>
              </div>
            ))}
          </div>
        )}

        {/* Actions */}
        <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: 16 }}>
          <h4 style={{ fontSize: 13, fontWeight: 700, color: '#374151', marginBottom: 10 }}>Actions</h4>
          <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
            <input style={{ ...inputStyle, flex: 1 }} placeholder="Author (optional)" value={author} onChange={e => setAuthor(e.target.value)} />
            <input style={{ ...inputStyle, flex: 2 }} placeholder="Comment (optional)" value={comment} onChange={e => setComment(e.target.value)} />
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button disabled={loading} onClick={() => handleStatus('approved')} style={btnStyle('#16a34a', '#fff')}>Approve</button>
            <button disabled={loading} onClick={() => handleStatus('rejected')} style={btnStyle('#dc2626', '#fff')}>Reject</button>
            <button disabled={loading} onClick={() => handleStatus('pending')} style={btnStyle('#d97706', '#fff')}>Set Pending</button>
            <button disabled={loading} onClick={handleDelete} style={{ ...btnStyle('#6b7280', '#fff'), marginLeft: 'auto' }}>Delete</button>
          </div>
        </div>
      </div>
    </div>
  );
}
