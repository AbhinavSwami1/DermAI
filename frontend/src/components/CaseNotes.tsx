import { useState, type SyntheticEvent } from "react";
import { apiRequest } from "../api/client";

type CaseData = { clinical_notes: string | null; follow_up_date: string | null };

export default function CaseNotes({ caseId }: { caseId: string }) {
  const [loaded, setLoaded] = useState(false);
  const [notes, setNotes] = useState("");
  const [followUp, setFollowUp] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function onToggle(e: SyntheticEvent<HTMLDetailsElement>) {
    if (!e.currentTarget.open || loaded) return;
    try {
      const c = await apiRequest<CaseData>(`/cases/${caseId}`);
      setNotes(c.clinical_notes ?? "");
      setFollowUp(c.follow_up_date ?? "");
      setLoaded(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load case notes.");
    }
  }

  async function save() {
    setSaving(true);
    setStatus("");
    setError("");
    try {
      await apiRequest(`/cases/${caseId}/notes`, {
        method: "PATCH",
        body: JSON.stringify({ clinical_notes: notes, follow_up_date: followUp || null }),
      });
      setStatus("Saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <details onToggle={onToggle} className="mt-4 rounded-md border border-slate-200 p-3">
      <summary className="cursor-pointer text-xs font-semibold text-slate-700">
        Case notes and follow-up
      </summary>
      <div className="mt-3 space-y-3">
        <p className="text-[11px] text-slate-500">
          Do not enter patient-identifiable information. Notes are visible only to the case owner.
        </p>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          maxLength={2000}
          rows={3}
          aria-label="Clinical notes"
          className="w-full rounded-md border border-slate-300 p-2 text-sm"
        />
        <div className="flex flex-wrap items-center gap-3">
          <label className="text-xs text-slate-600">
            Follow-up date{" "}
            <input type="date" value={followUp} onChange={(e) => setFollowUp(e.target.value)}
              className="ml-1 rounded-md border border-slate-300 px-2 py-1 text-sm" />
          </label>
          <button type="button" onClick={save} disabled={saving}
            className="rounded-md bg-cyan-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-cyan-800 disabled:opacity-60">
            {saving ? "Saving..." : "Save"}
          </button>
          <span className="text-[11px] text-slate-400">{notes.length}/2000</span>
        </div>
        {status && <p className="text-xs text-green-700">{status}</p>}
        {error && <p role="alert" className="text-xs text-red-700">{error}</p>}
      </div>
    </details>
  );
}
