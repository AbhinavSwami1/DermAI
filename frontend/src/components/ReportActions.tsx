import { useState } from "react";
import { Download, Loader2 } from "lucide-react";
import { apiGetBlob } from "../api/client";

type Fmt = "pdf" | "csv" | "json";

export default function ReportActions({ predictionId }: { predictionId: string }) {
  const [busy, setBusy] = useState<Fmt | null>(null);
  const [error, setError] = useState("");

  async function download(fmt: Fmt) {
    setBusy(fmt);
    setError("");
    try {
      const blob = await apiGetBlob(`/reports/${predictionId}?format=${fmt}`);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `dermai_report_${predictionId}.${fmt}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Report generation failed.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="mt-4">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold text-slate-600">Export report:</span>
        {(["pdf", "csv", "json"] as Fmt[]).map((f) => (
          <button key={f} onClick={() => download(f)} disabled={busy !== null}
            className="inline-flex items-center gap-1 rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium uppercase text-slate-700 hover:bg-slate-50 disabled:opacity-60">
            {busy === f ? <Loader2 size={13} className="animate-spin" /> : <Download size={13} />} {f}
          </button>
        ))}
      </div>
      {error && <p role="alert" className="mt-2 text-xs text-red-700">{error}</p>}
    </div>
  );
}
