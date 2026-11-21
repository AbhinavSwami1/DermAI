import { useState, type FormEvent } from "react";
import { Loader2 } from "lucide-react";
import { apiRequest, setAccessToken } from "../api/client";

interface LoginProps {
  onLoginSuccess: () => void;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
}

export default function Login({ onLoginSuccess }: LoginProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const data = await apiRequest<LoginResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      setAccessToken(data.access_token);
      onLoginSuccess();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to sign in. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  const field =
    "mt-1 w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-cyan-700 focus:outline-none";

  return (
    <main className="flex min-h-[80vh] items-center justify-center bg-stone-100 px-5 py-10">
      <section className="w-full max-w-sm rounded-md border border-slate-200 bg-white p-7">
        <p className="font-serif text-lg font-semibold text-slate-900">DermAI</p>
        <h1 className="mt-5 text-2xl font-semibold text-slate-900">Sign in</h1>
        <p className="mt-1 text-sm text-slate-500">
          Use the email and password you registered with.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <label htmlFor="email" className="block text-sm text-slate-700">
            Email
            <input
              id="email"
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className={field}
            />
          </label>

          <label htmlFor="password" className="block text-sm text-slate-700">
            Password
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className={field}
            />
          </label>

          {error && (
            <p role="alert" className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded bg-cyan-700 px-4 py-2.5 text-sm font-medium text-white hover:bg-cyan-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Signing in...
              </>
            ) : (
              "Sign in"
            )}
          </button>
        </form>

        <p className="mt-6 text-xs leading-5 text-slate-500">
          Research prototype. Not for clinical diagnosis or treatment.
        </p>
      </section>
    </main>
  );
}
