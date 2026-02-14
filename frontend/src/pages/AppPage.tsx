import { Sidebar } from '../components/Sidebar';
import { ChatWindow } from '../components/ChatWindow';

export function AppPage() {
  return (
    <div className="layout">
      <Sidebar />
      <ChatWindow />
    </div>
  );
}
