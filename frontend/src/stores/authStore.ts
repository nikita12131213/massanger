import { create } from 'zustand';
import { api } from '../api/client';
import type { User } from '../types';

interface AuthState {
  accessToken: string | null;
  me: User | null;
  setAccessToken: (token: string | null) => void;
  setMe: (user: User | null) => void;
  bootstrapMe: () => Promise<void>;
  refresh: () => Promise<string | null>;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  me: null,
  setAccessToken: (token) => set({ accessToken: token }),
  setMe: (user) => set({ me: user }),
  bootstrapMe: async () => {
    try {
      const { data } = await api.get('/api/auth/me');
      set({ me: data });
    } catch {
      set({ me: null });
    }
  },
  refresh: async () => {
    try {
      const { data } = await api.post('/api/auth/refresh');
      set({ accessToken: data.access_token });
      return data.access_token;
    } catch {
      set({ accessToken: null });
      return null;
    }
  }
}));
