import axios from 'axios';
import { useAuthStore } from '../stores/authStore';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (resp) => resp,
  async (err) => {
    if (err.response?.status === 401) {
      const t = await useAuthStore.getState().refresh();
      if (t) {
        err.config.headers.Authorization = `Bearer ${t}`;
        return api(err.config);
      }
    }
    throw err;
  }
);
