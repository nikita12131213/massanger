import { Link, useNavigate } from 'react-router-dom';
import { AuthForm } from '../components/AuthForm';
import { api } from '../api/client';

export function RegisterPage() {
  const navigate = useNavigate();
  return (
    <div className="center">
      <AuthForm
        title="Register"
        onSubmit={async (d) => {
          await api.post('/api/auth/register', d);
          navigate('/login');
        }}
      />
      <Link to="/login">Have account</Link>
    </div>
  );
}
