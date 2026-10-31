import { useState, type FormEvent } from "react";
import {
  ArrowRight,
  Loader2,
  LockKeyhole,
  Microscope,
  ShieldCheck,
} from "lucide-react";
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
        err instanceof Error
          ? err.message
          : "Unable to sign in. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#f5f7fb] px-5 py-10">
      <section className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-8 shadow-[0_12px_45px_rgba(15,23,42,0.07)] sm:p-10">
        <div className="mb-8 flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-400 text-[#101d35]">
            <Microscope size={26} />
          </div>

          <div>
            <h1 className="text-2xl font-bold text-slate-900">DermAI</h1>
            <p className="text-xs text-slate-500">Research Platform</p>
          </div>
        </div>

        <div className="mb-8">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-50 text-cyan-700">
            <LockKeyhole size={23} />
          </div>

          <h2 className="text-2xl font-bold text-slate-900">
            Welcome back
          </h2>

          <p className="mt-2 text-sm leading-6 text-slate-500">
            Sign in to access your experimental skin lesion research workspace.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label
              htmlFor="email"
              className="mb-2 block text-sm font-semibold text-slate-700"
            >
              Email address
            </label>

            <input
              id="email"
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
              className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-cyan-500 focus:ring-4 focus:ring-cyan-50"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="mb-2 block text-sm font-semibold text-slate-700"
            >
              Password
            </label>

            <input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter your password"
              className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-cyan-500 focus:ring-4 focus:ring-cyan-50"
            />
          </div>

          {error && (
            <div
              role="alert"
              className="rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700"
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#0f766e] px-5 py-3.5 text-sm font-semibold text-white shadow-lg transition hover:bg-[#115e59] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Signing in...
              </>
            ) : (
              <>
                Sign in to workspace
                <ArrowRight size={17} />
              </>
            )}
          </button>
        </form>

        <div className="mt-7 flex items-start gap-3 rounded-xl border border-cyan-100 bg-cyan-50/60 p-4">
          <ShieldCheck
            size={19}
            className="mt-0.5 shrink-0 text-cyan-700"
          />

          <p className="text-xs leading-5 text-slate-600">
            Secure research workspace. DermAI is an experimental academic
            prototype and is not intended for clinical diagnosis or treatment.
          </p>
        </div>

        <p className="mt-7 text-center text-xs text-slate-400">
          © 2026 DermAI · Academic Research Prototype
        </p>
      </section>
    </main>
  );
}