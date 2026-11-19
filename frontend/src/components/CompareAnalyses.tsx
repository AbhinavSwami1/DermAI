import { useEffect, useState } from "react";
import { apiGetBlob, apiRequest } from "../api/client";

interface Item {
  prediction_id: string;
  image_id: string;
  original_filename: string;
  predicted_label: string;
  confidence: number | null;
  model_version: string;
  created_at: string;
  top_predictions?: { rank: number; class_name: string; score: number }[] | null;
}

function Panel({ item }: { item: Item }) {
  const [src, setSrc] = useState<string | null>(null);
  useEffect(() => {
    let url: string | null = null;
    apiGetBlob(`/images/${item.image_id}/file`).then((b) => {
      url = URL.createObjectURL(b);
      setSrc(url);
    }).catch(() => setSrc(null));
    return () => { if (url) URL.revokeObjectURL(url); };
  }, [item.image_id]);

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs text-slate-500">{new Date(item.created_at).toLocaleString()}</p>
      {src ? <img src={src} alt={item.original_filename} className="mt-3 max-h-72 w-full rounded-md object-contain bg-slate-50" />
           : <p className="mt-3 text-sm text-slate-500">Image unavailable.</p>}
      <p className="mt-3 text-lg font-bold text-cyan-700">{item.predicted_label}</p>
      <p className="text-sm text-slate-600">Model score: {item.confidence !== null ? (item.confidence * 100).toFixed(2) + "%" : "n/a"}</p>
      <p className="text-xs text-slate-500">Model version: {item.model_version}</p>
      <ul className="mt-2 text-xs text-slate-600">
        {(item.top_predictions ?? []).map((t) => (
          <li key={t.rank}>{t.rank}. {t.class_name} - {(t.score * 100).toFixed(2)}%</li>
        ))}
      </ul>
    </div>
  );
}

export default function CompareAnalyses() {
  const [items, setItems] = useState<Item[]>([]);
  const [a, setA] = useState("");
  const [b, setB] = useState("");
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [error, setError] = useState("");

  useEffect(() => {
    apiRequest<{ items: Item[] }>("/predictions/history?page=1&page_size=50")
      .then((d) => { setItems(d.items); setState("ready"); })
      .catch((e) => { setError(e.message); setState("error"); });
  }, []);

  if (state === "loading") return <p className="text-sm text-slate-500">Loading analyses...</p>;
  if (state === "error") return <p role="alert" className="text-sm text-red-700">{error}</p>;
  if (items.length < 2) {
    return <p className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-600">
      At least two saved analyses are needed for comparison. Run another analysis first.</p>;
  }

  const ia = items.find((i) => i.prediction_id === a);
  const ib = items.find((i) => i.prediction_id === b);
  const opt = (i: Item) => `${new Date(i.created_at).toLocaleString()} - ${i.original_filename} - ${i.predicted_label}`;
  const sel = "w-full rounded-md border border-slate-300 px-3 py-2 text-sm";

  return (
    <section className="space-y-5">
      <h2 className="text-xl font-bold text-slate-900">Compare analyses</h2>
      <div className="grid gap-3 sm:grid-cols-2">
        <select className={sel} value={a} onChange={(e) => setA(e.target.value)} aria-label="First analysis">
          <option value="">Select first analysis</option>
          {items.map((i) => <option key={i.prediction_id} value={i.prediction_id}>{opt(i)}</option>)}
        </select>
        <select className={sel} value={b} onChange={(e) => setB(e.target.value)} aria-label="Second analysis">
          <option value="">Select second analysis</option>
          {items.map((i) => <option key={i.prediction_id} value={i.prediction_id}>{opt(i)}</option>)}
        </select>
      </div>
      {ia && ib && (
        <>
          <div className="grid gap-4 md:grid-cols-2"><Panel item={ia} /><Panel item={ib} /></div>
          {ia.model_version !== ib.model_version && (
            <p className="text-sm text-amber-800">These analyses used different model versions.</p>
          )}
        </>
      )}
      <p className="text-xs leading-5 text-slate-500">
        This view compares saved model outputs only. It does not indicate clinical improvement or deterioration.
      </p>
    </section>
  );
}
