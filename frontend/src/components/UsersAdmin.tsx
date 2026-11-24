import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../api/client";

type UserRow = { user_id: string; email: string; full_name: string; is_active: boolean; created_at: string; roles: string[] };

const ROLES = ["Patient", "Dermatologist", "Medical Researcher", "Data Scientist", "Administrator"];

export default function UsersAdmin() {
  const [users, setUsers] = useState<UserRow[] | null>(null);
  const [choice, setChoice] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState("");

  const load = useCallback(async () => {
    try {
      const data = await apiRequest<{ users: UserRow[] }>("/admin/users");
      setUsers(data.users);
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load users.");
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function assign(u: UserRow) {
    const role = choice[u.user_id] || "Dermatologist";
    setBusy(u.user_id); setNotice(""); setError("");
    try {
      await apiRequest(`/roles/users/${u.user_id}`, { method: "POST", body: JSON.stringify({ role_name: role }) });
      setNotice(`${role} assigned to ${u.email}.`);
      await load();
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to assign the role."); }
    finally { setBusy(""); }
  }

  async function revoke(u: UserRow, role: string) {
    setBusy(u.user_id); setNotice(""); setError("");
    try {
      await apiRequest(`/admin/users/${u.user_id}/roles/${encodeURIComponent(role)}`, { method: "DELETE" });
      setNotice(`${role} removed from ${u.email}.`);
      await load();
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to remove the role."); }
    finally { setBusy(""); }
  }

  if (!users && !error) return <p className="text-sm text-slate-500">Loading...</p>;

  return (
    <section className="space-y-4">
      <p className="text-sm text-slate-600">
        New accounts start as Patient. Staff roles are assigned here by an administrator. Role changes apply on the user&apos;s next page load.
      </p>
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      {notice && <p className="text-sm text-green-800">{notice}</p>}
      <div className="overflow-x-auto rounded-md border border-slate-200 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs text-slate-500">
            <tr><th className="p-3">User</th><th className="p-3">Roles</th><th className="p-3">Assign role</th></tr>
          </thead>
          <tbody>
            {users?.map((u) => (
              <tr key={u.user_id} className="border-t border-slate-100 align-top">
                <td className="p-3"><div className="font-medium text-slate-900">{u.full_name}</div><div className="text-xs text-slate-500">{u.email}</div></td>
                <td className="p-3">
                  <div className="flex flex-wrap gap-2">
                    {u.roles.length === 0 && <span className="text-xs text-slate-400">none</span>}
                    {u.roles.map((r) => (
                      <span key={r} className="inline-flex items-center gap-1 rounded border border-slate-300 px-2 py-0.5 text-xs">
                        {r}
                        <button type="button" aria-label={`Remove ${r} from ${u.email}`} disabled={busy === u.user_id}
                          onClick={() => revoke(u, r)} className="text-slate-400 hover:text-red-700">x</button>
                      </span>
                    ))}
                  </div>
                </td>
                <td className="p-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <select aria-label={`Role for ${u.email}`} className="rounded border border-slate-300 px-2 py-1 text-sm"
                      value={choice[u.user_id] ?? "Dermatologist"} onChange={(e) => setChoice({ ...choice, [u.user_id]: e.target.value })}>
                      {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                    </select>
                    <button type="button" disabled={busy === u.user_id} onClick={() => assign(u)}
                      className="rounded bg-cyan-700 px-3 py-1 text-xs font-medium text-white hover:bg-cyan-800 disabled:opacity-60">Assign</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
