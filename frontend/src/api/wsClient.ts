import { useAuthStore } from '../stores/authStore';

export class WSClient {
  ws: WebSocket | null = null;
  retries = 0;

  connect(onMessage: (e: MessageEvent) => void) {
    const token = useAuthStore.getState().accessToken;
    if (!token) return;
    const httpBase = import.meta.env.VITE_API_URL as string;
    const wsBase = httpBase.replace('http://', 'ws://').replace('https://', 'wss://');
    this.ws = new WebSocket(`${wsBase}/ws?token=${token}`);
    this.ws.onmessage = onMessage;
    this.ws.onclose = () => {
      const delay = Math.min(1000 * (this.retries + 1), 5000);
      this.retries += 1;
      setTimeout(() => this.connect(onMessage), delay);
    };
  }

  send(event: string, payload: Record<string, unknown>) {
    this.ws?.send(JSON.stringify({ event, payload }));
  }
}
