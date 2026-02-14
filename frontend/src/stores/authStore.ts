import { create } from 'zustand';
import { api } from '../api/client';

interface AuthState {
  accessToken: string | null;
  setAccessToken: (token: string | null) => void;
  refresh: () => Promise<string | null>;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  setAccessToken: (token) => set({ accessToken: token }),
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
