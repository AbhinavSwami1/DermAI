import { useCallback, useEffect, useState } from "react";
import { Bell } from "lucide-react";
import { apiRequest } from "../api/client";

type Notice = {
  id: string;
  level: string;
  title: string;
  message: string;
  created_at: string;
};

type Response = { count: number; items: Notice[]; note: string };

const levelLabel: Record<string, string> = {
  medium: "Medium",
  low: "Low",
  informational: "Info",
};

export default function NotificationBell({ refreshKey }: { refreshKey?: string }) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<Response | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      setData(await apiRequest<Response>("/notifications"));
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load notifications.");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  const attention = data ? data.items.filter((i) => i.level !== "informational").length : 0;

  return (
    <div className="relative">
      <button
        type="button"
        aria-label="Notifications"
        aria-expanded={open}
        onClick={() => { setOpen(!open); if (!open) load(); }}
        className="relative rounded-xl border border-slate-200 p-3 text-slate-500 hover:bg-slate-50"
      >
        <Bell size={19} />
        {attention > 0 && (
          <span className="absolute -right-1 -top-1 rounded-full bg-cyan-700 px-1.5 text-[10px] font-semibold text-white">
            {attention}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-30 mt-2 w-80 rounded-xl border border-slate-200 bg-white p-3 shadow-lg">
          <p className="text-sm font-semibold text-slate-900">Notifications</p>
          {error && <p role="alert" className="mt-2 text-xs text-red-700">{error}</p>}
          {data && data.items.length === 0 && (
            <p className="mt-2 text-xs text-slate-500">No notifications.</p>
          )}
          <ul className="mt-2 max-h-80 space-y-2 overflow-y-auto">
            {data?.items.map((n) => (
              <li key={n.id} className="rounded-lg border border-slate-100 p-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-semibold text-slate-800">{n.title}</span>
                  <span className="text-[10px] uppercase text-slate-500">{levelLabel[n.level] ?? n.level}</span>
                </div>
                <p className="mt-1 text-xs text-slate-600">{n.message}</p>
                <p className="mt-1 text-[10px] text-slate-400">{new Date(n.created_at).toLocaleString()}</p>
              </li>
            ))}
          </ul>
          {data && <p className="mt-2 text-[10px] text-slate-400">{data.note}</p>}
        </div>
      )}
    </div>
  );
}
