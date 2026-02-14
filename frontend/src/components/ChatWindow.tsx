import { useEffect, useMemo, useRef, useState } from 'react';
import { api } from '../api/client';
import { WSClient } from '../api/wsClient';
import { useAuthStore } from '../stores/authStore';
import { useChatStore } from '../stores/chatStore';
import type { Message } from '../types';

const ws = new WSClient();

export function ChatWindow() {
  const meToken = useAuthStore((s) => s.accessToken);
  const { activeConversationId, messages, setMessages, addMessage, ackMessage, typingUsers, setTyping } = useChatStore();
  const [text, setText] = useState('');
  const [before, setBefore] = useState<number | null>(null);
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
      <div className="messages">
        {currentMessages.map((m) => (
          <div key={`${m.id}-${m.temp_id ?? ''}`} className={`msg ${m.pending ? 'pending' : ''}`}>
            <div>{m.text}</div>
            {m.pending && <small>отправляется...</small>}
          </div>
        ))}
      </div>
      {typingUsers[activeConversationId]?.length ? <div>typing...</div> : null}
      <div className="composer">
        <textarea value={text} onChange={(e) => onTyping(e.target.value)} placeholder="message" />
        <input ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp" />
        <button onClick={upload}>Upload</button>
        <button onClick={send}>Send</button>
      </div>
    </main>
  );
}
