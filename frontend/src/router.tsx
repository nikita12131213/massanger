import { Navigate, Route, Routes } from 'react-router-dom';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { AppPage } from './pages/AppPage';
import { useAuthStore } from './stores/authStore';

export default function AppRouter() {
  const token = useAuthStore((s) => s.accessToken);

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/app" element={token ? <AppPage /> : <Navigate to="/login" />} />
      <Route path="*" element={<Navigate to={token ? '/app' : '/login'} />} />
    </Routes>
  );
}
