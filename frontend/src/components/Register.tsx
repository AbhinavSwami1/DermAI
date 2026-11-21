import { useState, type FormEvent } from "react";
import { Loader2 } from "lucide-react";
import { apiRequest } from "../api/client";

interface Props {
  onRegistered: () => void;
  onLogin: () => void;
  onBack: () => void;
}

export default function Register({ onRegistered, onLogin, onBack }: Props) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await apiRequest("/users/register", {
        method: "POST",
        body: JSON.stringify({ full_name: fullName, email, password }),
      });
      onRegistered();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed.");
    } finally {
      setLoading(false);
    }
  }

  const field = "mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-cyan-700 focus:outline-none";

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-5">
      <form onSubmit={submit} className="w-full max-w-sm space-y-4 rounded-md border border-slate-200 bg-white p-6">
        <h1 className="text-xl font-bold text-slate-900">Create an account</h1>
        <label className="block text-sm text-slate-700">Full name
          <input className={field} value={fullName} onChange={(e) => setFullName(e.target.value)} required minLength={2} />
        </label>
        <label className="block text-sm text-slate-700">Email
          <input type="email" className={field} value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label className="block text-sm text-slate-700">Password (min. 8 characters)
          <input type="password" className={field} value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />
        </label>
        {error && <p role="alert" className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        <button disabled={loading} className="flex w-full items-center justify-center gap-2 rounded-md bg-cyan-700 py-2.5 text-sm font-semibold text-white hover:bg-cyan-800 disabled:opacity-60">
          {loading && <Loader2 size={16} className="animate-spin" />} Register
        </button>
        <div className="flex justify-between text-sm">
          <button type="button" onClick={onLogin} className="text-cyan-700 hover:underline">Already registered? Log in</button>
          <button type="button" onClick={onBack} className="text-slate-500 hover:underline">Back</button>
        </div>
      </form>
    </div>
  );
}
