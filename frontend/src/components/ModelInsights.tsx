import { useEffect, useState } from "react";
import { apiRequest } from "../api/client";

interface Resp {
  available: boolean;
  model_version: string | null;
  test_metrics: Record<string, unknown> | null;
  source?: string;
}

const label = (k: string) => k.replace(/_/g, " ");

export default function ModelInsights() {
  const [d, setD] = useState<Resp | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    apiRequest<Resp>("/insights/model-metrics").then(setD).catch((e) => setError(e.message));
  }, []);

  if (error) return <p role="alert" className="text-sm text-red-700">{error}</p>;
  if (!d) return <p className="text-sm text-slate-500">Loading...</p>;

  const scalars = Object.entries(d.test_metrics ?? {}).filter(([, v]) => typeof v === "number");
  const pct = (v: number) => (v <= 1 ? (v * 100).toFixed(2) + "%" : String(v));

  return (
    <section className="space-y-5">
      <h2 className="text-xl font-bold text-slate-900">Research insights</h2>
      <p className="text-sm text-slate-600">Model version: {d.model_version ?? "n/a"}</p>
      {!d.available ? (
        <p className="rounded-md border border-slate-200 bg-white p-5 text-sm text-slate-600">
          Evaluation results are not available on this server. Run the evaluation script to generate
          ml/outputs/mobilenet_v3_large_finetuned/test_metrics.json.
        </p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {scalars.map(([k, v]) => (
            <div key={k} className="rounded-md border border-slate-200 bg-white p-4">
              <p className="text-xs capitalize text-slate-500">{label(k)}</p>
              <p className="mt-1 text-xl font-bold text-slate-900">{pct(v as number)}</p>
            </div>
          ))}
        </div>
      )}
      <p className="text-xs leading-5 text-slate-500">
        Held-out test results from a research experiment. Grad-CAM is not segmentation. Predictions must
        not be used for medical diagnosis or treatment decisions.
        {d.source ? ` Source: ${d.source}.` : ""}
      </p>
    </section>
  );
}
