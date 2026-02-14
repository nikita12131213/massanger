import { useForm } from 'react-hook-form';
import { z } from 'zod';

const schema = z.object({ username: z.string().min(3), password: z.string().min(6) });

type FormData = z.infer<typeof schema>;

export function AuthForm({ onSubmit, title }: { onSubmit: (d: FormData) => Promise<void>; title: string }) {
  const { register, handleSubmit, setError, formState } = useForm<FormData>();
  return (
    <form
      className="card"
      onSubmit={handleSubmit(async (values) => {
        const result = schema.safeParse(values);
        if (!result.success) {
          result.error.issues.forEach((i) => setError(i.path[0] as keyof FormData, { message: i.message }));
          return;
        }
        await onSubmit(result.data);
      })}
    >
      <h2>{title}</h2>
      <input placeholder="username" {...register('username')} />
      <input placeholder="password" type="password" {...register('password')} />
      <button type="submit">Submit</button>
      {formState.errors.username && <p>{formState.errors.username.message}</p>}
      {formState.errors.password && <p>{formState.errors.password.message}</p>}
    </form>
  );
}
