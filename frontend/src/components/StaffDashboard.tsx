import { useEffect, useState } from "react";
import { apiRequest } from "../api/client";

type Dict = Record<string, any>;

function Stat({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-4">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{String(value ?? "n/a")}</p>
    </div>
  );
}

function CountTable({ title, data }: { title: string; data: Record<string, number> }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-4">
      <h3 className="text-sm font-semibold">{title}</h3>
      <table className="mt-2 w-full text-sm"><tbody>
        {Object.entries(data).map(([k, v]) => (
          <tr key={k} className="border-t border-slate-100"><td className="py-1">{k.replace(/_/g, " ")}</td><td className="py-1 text-right">{String(v)}</td></tr>
        ))}
      </tbody></table>
    </div>
  );
}

function ModelUsage({ rows }: { rows: Dict[] }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-4">
      <h3 className="text-sm font-semibold">Model usage</h3>
      <table className="mt-2 w-full text-sm"><tbody>
        {rows.map((m) => (
          <tr key={m.version} className="border-t border-slate-100"><td className="py-1">{m.model_name} ({m.version})</td><td className="py-1 text-right">{m.analyses}</td></tr>
        ))}
      </tbody></table>
    </div>
  );
}

export default function StaffDashboard() {
  const [roles, setRoles] = useState<string[] | null>(null);
  const [clin, setClin] = useState<Dict | null>(null);
  const [research, setResearch] = useState<Dict | null>(null);
  const [admin, setAdmin] = useState<Dict | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    apiRequest<{ roles: string[] }>("/roles/me").then(async (r) => {
      setRoles(r.roles);
      const has = (...names: string[]) => names.some((n) => r.roles.includes(n));
      try {
        if (has("Dermatologist", "Administrator")) setClin(await apiRequest<Dict>("/dashboard/clinician"));
        if (has("Medical Researcher", "Data Scientist", "Administrator")) setResearch(await apiRequest<Dict>("/dashboard/research"));
        if (has("Administrator")) setAdmin(await apiRequest<Dict>("/dashboard/admin"));
      } catch (e) { setError(e instanceof Error ? e.message : "Failed to load."); }
    }).catch((e) => setError(e.message));
  }, []);

  if (error) return <p role="alert" className="text-sm text-red-700">{error}</p>;
  if (!roles) return <p className="text-sm text-slate-500">Loading...</p>;
  if (!clin && !research && !admin) {
    return <p className="rounded-md border border-slate-200 bg-white p-6 text-sm text-slate-600">
      Dashboards are available to the Dermatologist, Medical Researcher, Data Scientist and Administrator roles. Your roles: {roles.join(", ") || "none"}.</p>;
  }

  return (
    <section className="space-y-10">
      {clin && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-slate-900">Clinician dashboard</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Stat label="Total cases" value={clin.total_cases} />
            <Stat label="Total analyses" value={clin.total_analyses} />
            <Stat label="Average model score" value={clin.average_model_score != null ? (clin.average_model_score * 100).toFixed(1) + "%" : "n/a"} />
            <Stat label={`Scores below ${clin.low_score_threshold} (review suggested)`} value={clin.low_score_analyses} />
          </div>
          <CountTable title="Predicted class distribution" data={clin.predicted_class_distribution} />
          <div className="overflow-x-auto rounded-md border border-slate-200 bg-white p-4">
            <h3 className="text-sm font-semibold">Recent analyses</h3>
            <table className="mt-2 w-full text-left text-sm">
              <thead className="text-xs text-slate-500"><tr><th>Date</th><th>Case</th><th>Class</th><th>Score</th></tr></thead>
              <tbody>{clin.recent_analyses.map((r: Dict) => (
                <tr key={r.prediction_id} className="border-t border-slate-100">
                  <td className="py-1">{new Date(r.created_at).toLocaleString()}</td>
                  <td className="py-1 font-mono text-xs">{r.case_id.slice(0, 8)}</td>
                  <td className="py-1">{r.predicted_label}</td>
                  <td className="py-1">{(r.confidence * 100).toFixed(1)}%</td>
                </tr>))}</tbody>
            </table>
          </div>
          <p className="text-xs text-slate-500">{clin.note}</p>
        </div>
      )}
      {research && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-slate-900">Research dashboard</h2>
          <p className="text-sm text-slate-500">De-identified aggregates. No user, case or image identifiers are shown.</p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Stat label="Total analyses" value={research.total_analyses} />
            {Object.entries(research.score_bands as Record<string, number>).map(([k, v]) => (
              <Stat key={k} label={`Model score ${k.replace(/_/g, " ")}`} value={v} />
            ))}
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <CountTable title="Predicted class distribution" data={research.predicted_class_distribution} />
            <CountTable title="Image quality status" data={research.image_quality_status} />
          </div>
          <ModelUsage rows={research.model_usage} />
          <p className="text-xs text-slate-500">{research.note}</p>
        </div>
      )}
      {admin && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-slate-900">Administrator dashboard</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <Stat label="Registered users" value={admin.registered_users} />
            <Stat label="Cases" value={admin.total_cases} />
            <Stat label="Images" value={admin.total_images} />
            <Stat label="Analyses" value={admin.total_analyses} />
            <Stat label="Analyses, last 7 days" value={admin.analyses_last_7_days} />
          </div>
          <ModelUsage rows={admin.model_usage} />
        </div>
      )}
    </section>
  );
}
