import { create } from 'zustand';
import type { Conversation, Message } from '../types';

interface ChatState {
  conversations: Conversation[];
  activeConversationId: number | null;
  messages: Record<number, Message[]>;
  typingUsers: Record<number, number[]>;
  setConversations: (items: Conversation[]) => void;
  setActiveConversation: (id: number) => void;
  setMessages: (conversationId: number, items: Message[]) => void;
  addMessage: (conversationId: number, item: Message) => void;
  ackMessage: (conversationId: number, tempId: string, messageId: number, createdAt: string) => void;
  setTyping: (conversationId: number, userId: number, on: boolean) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  activeConversationId: null,
  messages: {},
  typingUsers: {},
  setConversations: (items) => set({ conversations: items }),
  setActiveConversation: (id) => set({ activeConversationId: id }),
  setMessages: (conversationId, items) => set((s) => ({ messages: { ...s.messages, [conversationId]: items } })),
  addMessage: (conversationId, item) =>
    set((s) => ({ messages: { ...s.messages, [conversationId]: [...(s.messages[conversationId] ?? []), item] } })),
  ackMessage: (conversationId, tempId, messageId, createdAt) => {
    const items = (get().messages[conversationId] ?? []).map((m) =>
      m.temp_id === tempId ? { ...m, id: messageId, created_at: createdAt, pending: false } : m
    );
    set((s) => ({ messages: { ...s.messages, [conversationId]: items } }));
  },
  setTyping: (conversationId, userId, on) =>
    set((s) => {
      const arr = new Set(s.typingUsers[conversationId] ?? []);
      on ? arr.add(userId) : arr.delete(userId);
      return { typingUsers: { ...s.typingUsers, [conversationId]: [...arr] } };
    })
}));
