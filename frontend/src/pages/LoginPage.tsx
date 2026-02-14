import { Link, useNavigate } from 'react-router-dom';
import { AuthForm } from '../components/AuthForm';
import { api } from '../api/client';
import { useAuthStore } from '../stores/authStore';

export function LoginPage() {
  const navigate = useNavigate();
  const setAccessToken = useAuthStore((s) => s.setAccessToken);
  return (
    <div className="center">
      <AuthForm
        title="Login"
        onSubmit={async (d) => {
          const { data } = await api.post('/api/auth/login', d);
          setAccessToken(data.access_token);
          navigate('/app');
        }}
      />
      <Link to="/register">Create account</Link>
    </div>
  );
}
