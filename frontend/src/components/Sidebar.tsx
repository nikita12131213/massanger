import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { useChatStore } from '../stores/chatStore';
import type { User } from '../types';

export function Sidebar() {

  const [q, setQ] = useState('');
  const [results, setResults] = useState<User[]>([]);

  useEffect(() => {
    api.get('/api/conversations').then((r) => setConversations(r.data));
  }, [setConversations]);


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
          <div>{c.last_message?.text?.slice(0, 24) ?? 'No messages yet'}</div>
          {c.unread_count > 0 && <span className="badge">{c.unread_count}</span>}
        </div>
      ))}
    </aside>
  );
}
