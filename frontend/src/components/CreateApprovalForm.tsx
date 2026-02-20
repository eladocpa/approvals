import React, { useState } from 'react';
import { CreateApprovalDto } from '../types';

interface Props {
  onSubmit: (data: CreateApprovalDto) => Promise<void>;
  onCancel: () => void;
}

export function CreateApprovalForm({ onSubmit, onCancel }: Props) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [requestedBy, setRequestedBy] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!title.trim() || !description.trim() || !requestedBy.trim()) {
      setError('All fields are required.');
      return;
    }
    setLoading(true);
    try {
      await onSubmit({ title: title.trim(), description: description.trim(), requestedBy: requestedBy.trim() });
    } catch {
      setError('Failed to create approval. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '8px 12px',
    border: '1px solid #d1d5db',
    borderRadius: 6,
    fontSize: 14,
    outline: 'none',
  };

  const labelStyle: React.CSSProperties = {
    display: 'block',
    fontSize: 13,
    fontWeight: 600,
    color: '#374151',
    marginBottom: 4,
  };

  return (
    <form onSubmit={handleSubmit} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: 24, marginBottom: 24 }}>
      <h3 style={{ marginBottom: 16, fontSize: 16, fontWeight: 700 }}>New Approval Request</h3>
      {error && <div style={{ color: '#dc2626', marginBottom: 12, fontSize: 13 }}>{error}</div>}
      <div style={{ marginBottom: 12 }}>
        <label style={labelStyle}>Title</label>
        <input style={inputStyle} value={title} onChange={e => setTitle(e.target.value)} placeholder="Brief title" />
      </div>
      <div style={{ marginBottom: 12 }}>
        <label style={labelStyle}>Description</label>
        <textarea
          style={{ ...inputStyle, minHeight: 80, resize: 'vertical' }}
          value={description}
          onChange={e => setDescription(e.target.value)}
          placeholder="Describe the request..."
        />
      </div>
      <div style={{ marginBottom: 16 }}>
        <label style={labelStyle}>Requested By</label>
        <input style={inputStyle} value={requestedBy} onChange={e => setRequestedBy(e.target.value)} placeholder="Your name" />
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        <button
          type="submit"
          disabled={loading}
          style={{ background: '#2563eb', color: '#fff', border: 'none', borderRadius: 6, padding: '8px 18px', fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1 }}
        >
          {loading ? 'Submitting...' : 'Submit'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          style={{ background: '#f3f4f6', color: '#374151', border: '1px solid #d1d5db', borderRadius: 6, padding: '8px 18px', fontWeight: 600, cursor: 'pointer' }}
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
