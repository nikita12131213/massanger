import { create } from 'zustand';
import { api } from '../api/client';
  refresh: () => Promise<string | null>;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
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
