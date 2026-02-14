import { type KeyboardEvent, useEffect, useMemo, useRef, useState } from 'react';
import { api } from '../api/client';
import { WSClient } from '../api/wsClient';
import { useAuthStore } from '../stores/authStore';
import { useChatStore } from '../stores/chatStore';
import type { Message } from '../types';

const ws = new WSClient();

export function ChatWindow() {
  const meToken = useAuthStore((s) => s.accessToken);
  const me = useAuthStore((s) => s.me);
  const { activeConversationId, messages, setMessages, addMessage, ackMessage, typingUsers, setTyping, updateMessage, removeMessage } =
    useChatStore();
  const [text, setText] = useState('');
  const [before, setBefore] = useState<number | null>(null);
  const [search, setSearch] = useState('');
  const [searchResults, setSearchResults] = useState<Message[]>([]);
  const fileRef = useRef<HTMLInputElement | null>(null);

  const currentMessages = useMemo(() => messages[activeConversationId ?? -1] ?? [], [messages, activeConversationId]);

  useEffect(() => {
    if (!meToken) return;
    ws.connect((evt) => {
      const data = JSON.parse(evt.data);
      if (data.event === 'message:ack' && activeConversationId) {
        ackMessage(activeConversationId, data.payload.temp_id, data.payload.message_id, data.payload.created_at);
      }
      if (data.event === 'message:new') {
        const m = data.payload.message as Message;
        addMessage(m.conversation_id, m);
      }
      if (data.event === 'typing:start') setTyping(data.payload.conversation_id, data.payload.user_id, true);
      if (data.event === 'typing:stop') setTyping(data.payload.conversation_id, data.payload.user_id, false);
    });
  }, [meToken, activeConversationId, addMessage, ackMessage, setTyping]);

  useEffect(() => {
    if (!activeConversationId) return;
    api.get('/api/messages', { params: { conversation_id: activeConversationId, limit: 20 } }).then((r) => {
      setMessages(activeConversationId, r.data.reverse());
      if (r.data.length) setBefore(r.data[r.data.length - 1].id);
      api.post(`/api/conversations/${activeConversationId}/read`).catch(() => undefined);
    });
  }, [activeConversationId, setMessages]);

  const loadMore = async () => {
    if (!activeConversationId || !before) return;
    const { data } = await api.get('/api/messages', { params: { conversation_id: activeConversationId, before, limit: 20 } });
    const incoming = [...data].reverse();
    setMessages(activeConversationId, [...incoming, ...currentMessages]);
    if (data.length) setBefore(data[data.length - 1].id);
  };

  const send = () => {
    if (!activeConversationId || !text.trim()) return;
    const tempId = crypto.randomUUID();
    addMessage(activeConversationId, { id: -Date.now(), temp_id: tempId, pending: true, conversation_id: activeConversationId, sender_id: 0, text, created_at: new Date().toISOString(), attachments: [] });
    ws.send('message:send', { temp_id: tempId, conversation_id: activeConversationId, text });
    setText('');
  };

  const onTyping = (value: string) => {
    setText(value);
    if (!activeConversationId) return;
    ws.send('typing:start', { conversation_id: activeConversationId });
    window.clearTimeout((window as any).__typingTimer);
    (window as any).__typingTimer = window.setTimeout(() => ws.send('typing:stop', { conversation_id: activeConversationId }), 800);
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const onSearch = async () => {
    if (!activeConversationId || !search.trim()) {
      setSearchResults([]);
      return;
    }
    const { data } = await api.get('/api/messages/search', { params: { conversation_id: activeConversationId, q: search } });
    setSearchResults(data);
  };

  const onEdit = async (messageId: number, prevText: string) => {
    const next = window.prompt('Edit message', prevText);
    if (!next || next.trim() === prevText) return;
    await api.patch(`/api/messages/${messageId}`, { text: next.trim() });
    if (activeConversationId) updateMessage(activeConversationId, messageId, next.trim());
  };

  const onDelete = async (messageId: number) => {
    await api.delete(`/api/messages/${messageId}`);
    if (activeConversationId) removeMessage(activeConversationId, messageId);
  };

  const upload = async () => {
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.append('file', file);
    const { data } = await api.post('/api/attachments', form);
    setText((t) => `${t} ${data.url}`.trim());
  };

  if (!activeConversationId) return <main className="chat">Select a dialog</main>;

  return (
    <main className="chat">
      <button onClick={loadMore}>Загрузить ещё</button>
      <div className="search-row">
        <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="search in chat" />
        <button onClick={onSearch}>Search</button>
      </div>
      {searchResults.length > 0 && (
        <div className="search-results">
          {searchResults.slice(0, 5).map((m) => (
            <div key={`search-${m.id}`} className="list-item">
              {m.text}
            </div>
          ))}
        </div>
      )}
      <div className="messages">
        {currentMessages.map((m) => (
          <div key={`${m.id}-${m.temp_id ?? ''}`} className={`msg ${m.pending ? 'pending' : ''}`}>
            <div>{m.text}</div>
            {m.text.startsWith('/media/') && <img src={`${import.meta.env.VITE_API_URL}${m.text}`} style={{ maxWidth: 220, marginTop: 8 }} />}
            {m.sender_id === me?.id && !m.pending && (
              <div style={{ marginTop: 6, display: 'flex', gap: 6 }}>
                <button onClick={() => onEdit(m.id, m.text)}>edit</button>
                <button onClick={() => onDelete(m.id)}>delete</button>
              </div>
            )}
            {m.pending && <small>отправляется...</small>}
          </div>
        ))}
      </div>
      {(typingUsers[activeConversationId] ?? []).filter((id) => id !== me?.id).length ? <div>typing...</div> : null}
      <div className="composer">
        <textarea value={text} onChange={(e) => onTyping(e.target.value)} onKeyDown={onKeyDown} placeholder="message" />
        <input ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp" />
        <button onClick={upload}>Upload</button>
        <button onClick={send}>Send</button>
      </div>
    </main>
  );
}
