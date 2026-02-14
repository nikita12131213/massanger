import { useEffect } from 'react';
import { Sidebar } from '../components/Sidebar';
import { ChatWindow } from '../components/ChatWindow';
import { useAuthStore } from '../stores/authStore';

export function AppPage() {
  const me = useAuthStore((s) => s.me);
  const bootstrapMe = useAuthStore((s) => s.bootstrapMe);

  useEffect(() => {
    if (!me) {
      bootstrapMe();
    }
  }, [me, bootstrapMe]);

  return (
    <div className="layout">
      <Sidebar />
      <ChatWindow />
    </div>
  );
}
