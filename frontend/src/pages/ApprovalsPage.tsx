import React, { useCallback, useEffect, useState } from 'react';
import { Approval, ApprovalStatus, CreateApprovalDto } from '../types';
import { ApprovalCard } from '../components/ApprovalCard';
import { ApprovalDetail } from '../components/ApprovalDetail';
import { CreateApprovalForm } from '../components/CreateApprovalForm';

const API = '/api/approvals';

export function ApprovalsPage() {
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [selected, setSelected] = useState<Approval | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState<ApprovalStatus | 'all'>('all');

  const fetchAll = useCallback(async () => {
    try {
      const res = await fetch(API);
      if (!res.ok) throw new Error('Failed to load');
      setApprovals(await res.json());
    } catch {
      setError('Could not load approvals.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleCreate = async (data: CreateApprovalDto) => {
    const res = await fetch(API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Create failed');
    setShowForm(false);
    await fetchAll();
  };

  const handleUpdateStatus = async (id: string, status: ApprovalStatus, comment?: string, author?: string) => {
    const res = await fetch(`${API}/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, comment, author }),
    });
    if (!res.ok) throw new Error('Update failed');
    const updated: Approval = await res.json();
    setSelected(updated);
    setApprovals(prev => prev.map(a => a.id === id ? updated : a));
  };

  const handleDelete = async (id: string) => {
    await fetch(`${API}/${id}`, { method: 'DELETE' });
    setSelected(null);
    setApprovals(prev => prev.filter(a => a.id !== id));
  };

  const filtered = filter === 'all' ? approvals : approvals.filter(a => a.status === filter);

  if (loading) return <div style={{ padding: 40, textAlign: 'center', color: '#6b7280' }}>Loading...</div>;

  if (selected) {
    return (
      <ApprovalDetail
        approval={selected}
        onUpdateStatus={handleUpdateStatus}
        onDelete={handleDelete}
        onBack={() => setSelected(null)}
      />
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>Approvals</h1>
        <button
          onClick={() => setShowForm(f => !f)}
          style={{ background: '#2563eb', color: '#fff', border: 'none', borderRadius: 6, padding: '8px 18px', fontWeight: 600, cursor: 'pointer' }}
        >
          {showForm ? 'Cancel' : '+ New Request'}
        </button>
      </div>

      {showForm && <CreateApprovalForm onSubmit={handleCreate} onCancel={() => setShowForm(false)} />}

      {error && <div style={{ color: '#dc2626', marginBottom: 16 }}>{error}</div>}

      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {(['all', 'pending', 'approved', 'rejected'] as const).map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            style={{
              padding: '5px 14px', borderRadius: 20, border: '1px solid #d1d5db', cursor: 'pointer',
              fontWeight: filter === f ? 700 : 400,
              background: filter === f ? '#2563eb' : '#fff',
              color: filter === f ? '#fff' : '#374151',
              fontSize: 13,
            }}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)} ({f === 'all' ? approvals.length : approvals.filter(a => a.status === f).length})
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#9ca3af', padding: 40 }}>No approvals found.</div>
      ) : (
        filtered.map(a => <ApprovalCard key={a.id} approval={a} onClick={setSelected} />)
      )}
    </div>
  );
}
