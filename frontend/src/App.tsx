import React from 'react';
import { ApprovalsPage } from './pages/ApprovalsPage';

function App() {
  return (
    <div style={{ minHeight: '100vh', background: '#f3f4f6' }}>
      <header style={{ background: '#1e40af', color: '#fff', padding: '14px 0', marginBottom: 32, boxShadow: '0 2px 6px rgba(0,0,0,0.15)' }}>
        <div style={{ maxWidth: 800, margin: '0 auto', padding: '0 20px', display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 20, fontWeight: 800, letterSpacing: 0.5 }}>Approvals</span>
          <span style={{ fontSize: 12, opacity: 0.7, marginTop: 2 }}>Management System</span>
        </div>
      </header>
      <main style={{ maxWidth: 800, margin: '0 auto', padding: '0 20px 40px' }}>
        <ApprovalsPage />
      </main>
    </div>
  );
}

export default App;
