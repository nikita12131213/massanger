import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { useChatStore } from '../stores/chatStore';
import type { User } from '../types';

export function Sidebar() {
  const { conversations, setConversations, setActiveConversation, setPresence, presence } = useChatStore();
  const [q, setQ] = useState('');
  const [results, setResults] = useState<User[]>([]);

  useEffect(() => {
    api.get('/api/conversations').then((r) => setConversations(r.data));
  }, [setConversations]);

  useEffect(() => {
    const refreshPresence = async () => {
      const peerIds = conversations.map((c) => c.peer?.id).filter(Boolean) as number[];
      if (!peerIds.length) return;
      const { data } = await api.get('/api/users/presence', { params: { ids: peerIds.join(',') } });
      const mapped = Object.fromEntries(Object.entries(data.presence).map(([k, v]) => [Number(k), Boolean(v)]));
      setPresence(mapped);
    };
    refreshPresence();
    const t = window.setInterval(refreshPresence, 10000);
    return () => window.clearInterval(t);
  }, [conversations, setPresence]);

  const search = async () => {
    if (!q) return;
    const { data } = await api.get('/api/users/search', { params: { q } });
    setResults(data);
  };

  const createDialog = async (username: string) => {
    const { data } = await api.post('/api/conversations', { username });
    setActiveConversation(data.id);
    const refresh = await api.get('/api/conversations');
    setConversations(refresh.data);
  };

  return (
    <aside className="sidebar">
      <div className="search-row">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="find user" />
        <button onClick={search}>New dialog</button>
      </div>
      {results.map((u) => (
        <div key={u.id} className="list-item" onClick={() => createDialog(u.username)}>
          @{u.username}
        </div>
      ))}
      <hr />
      {conversations.map((c) => (
        <div key={c.id} className="list-item" onClick={() => setActiveConversation(c.id)}>
          <strong>
            {c.peer?.username ?? 'Unknown'}
            {c.peer?.id && <span style={{ marginLeft: 8, color: presence[c.peer.id] ? '#34d399' : '#9ca3af' }}>●</span>}
          </strong>
          <div>{c.last_message?.text?.slice(0, 24) ?? 'No messages yet'}</div>
          {c.unread_count > 0 && <span className="badge">{c.unread_count}</span>}
        </div>
      ))}
    </aside>
  );
}
