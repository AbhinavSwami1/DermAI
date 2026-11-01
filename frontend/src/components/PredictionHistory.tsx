import { useCallback, useEffect, useState } from "react";
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  Clock3,
  FileImage,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";
import { apiRequest } from "../api/client";

type PredictionHistoryItem = {
  prediction_id: string;
  case_id: string;
  image_id: string;
  original_filename: string;
  predicted_label: string;
  confidence: number | null;
  class_scores: Record<string, number> | null;
  status: string;
  model_version_id: string;
  model_name: string;
  model_version: string;
  architecture: string;
  created_at: string;
};

type PredictionHistoryResponse = {
  items: PredictionHistoryItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  disclaimer: string;
};

const classNames: Record<string, string> = {
  ACK: "Actinic Keratosis",
  BCC: "Basal Cell Carcinoma",
  MEL: "Melanoma",
  NEV: "Melanocytic Nevus",
  SCC: "Squamous Cell Carcinoma",
  SEK: "Seborrheic Keratosis",
};

function formatDate(value: string) {
  return new Date(value).toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export default function PredictionHistory() {
  const [history, setHistory] =
    useState<PredictionHistoryResponse | null>(null);

  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const pageSize = 10;

  const loadHistory = useCallback(async (requestedPage: number) => {
    setLoading(true);
    setError("");

    try {
      const result = await apiRequest<PredictionHistoryResponse>(
        `/predictions/history?page=${requestedPage}&page_size=${pageSize}`,
      );

      setHistory(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load prediction history.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadHistory(page);
  }, [page, loadHistory]);

  return (
    <section className="space-y-6">
      {/* Page heading */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-cyan-700">
            Research Workspace / Records
          </p>

          <h2 className="mt-2 text-2xl font-bold text-slate-900 sm:text-3xl">
            Analysis History
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Review previously saved experimental model predictions.
          </p>
        </div>

        <button
          onClick={() => loadHistory(page)}
          disabled={loading}
          className="flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
        >
          <RefreshCw
            size={16}
            className={loading ? "animate-spin" : ""}
          />
          Refresh
        </button>
      </div>

      {/* Summary */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-500">
              Total Predictions
            </span>
            <FileImage className="text-cyan-700" size={21} />
          </div>

          <p className="mt-4 text-3xl font-bold text-slate-900">
            {history?.total ?? "—"}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-500">
              Current Page
            </span>
            <Clock3 className="text-cyan-700" size={21} />
          </div>

          <p className="mt-4 text-3xl font-bold text-slate-900">
            {history ? `${history.page} / ${Math.max(history.total_pages, 1)}` : "—"}
          </p>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="rounded-2xl border border-slate-200 bg-white p-12 text-center">
          <RefreshCw
            className="mx-auto animate-spin text-cyan-700"
            size={30}
          />
          <p className="mt-4 text-sm text-slate-500">
            Loading prediction history...
          </p>
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-6">
          <div className="flex items-center gap-3 text-red-700">
            <AlertCircle size={22} />
            <h3 className="font-semibold">
              Unable to load history
            </h3>
          </div>

          <p className="mt-3 text-sm text-red-600">
            {error}
          </p>

          <button
            onClick={() => loadHistory(page)}
            className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && history?.items.length === 0 && (
        <div className="rounded-2xl border border-slate-200 bg-white px-6 py-16 text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-cyan-50 text-cyan-700">
            <FileImage size={30} />
          </div>

          <h3 className="mt-5 text-lg font-bold text-slate-900">
            No predictions yet
          </h3>

          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">
            Your completed experimental image predictions will appear here.
            Start a new analysis to create your first record.
          </p>
        </div>
      )}

      {/* Prediction cards */}
      {!loading && !error && history && history.items.length > 0 && (
        <div className="space-y-4">
          {history.items.map((item) => (
            <article
              key={item.prediction_id}
              className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"
            >
              <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-lg bg-cyan-50 px-3 py-1.5 text-xs font-bold text-cyan-800">
                      {item.predicted_label}
                    </span>

                    <span className="rounded-lg bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700">
                      {item.status}
                    </span>
                  </div>

                  <h3 className="mt-4 break-all text-base font-bold text-slate-900">
                    {item.original_filename}
                  </h3>

                  <p className="mt-2 text-xs text-slate-500">
                    {classNames[item.predicted_label] ?? item.predicted_label}
                  </p>

                  <p className="mt-3 flex items-center gap-2 text-xs text-slate-400">
                    <Clock3 size={14} />
                    {formatDate(item.created_at)}
                  </p>
                </div>

                <div className="rounded-xl bg-slate-50 p-4 sm:min-w-36 sm:text-right">
                  <p className="text-xs font-medium text-slate-500">
                    Model confidence
                  </p>

                  <p className="mt-2 text-2xl font-bold text-cyan-800">
                    {item.confidence !== null
                      ? `${(item.confidence * 100).toFixed(2)}%`
                      : "N/A"}
                  </p>
                </div>
              </div>

              {/* Model information */}
              <div className="mt-5 grid gap-3 border-t border-slate-100 pt-5 sm:grid-cols-3">
                <div>
                  <p className="text-xs text-slate-400">
                    Architecture
                  </p>
                  <p className="mt-1 text-sm font-semibold text-slate-700">
                    {item.architecture}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-400">
                    Model version
                  </p>
                  <p className="mt-1 break-all text-sm font-semibold text-slate-700">
                    {item.model_version}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-400">
                    Case reference
                  </p>
                  <p className="mt-1 break-all text-sm font-semibold text-slate-700">
                    {item.case_id.slice(0, 8)}...
                  </p>
                </div>
              </div>

              {/* Expandable class scores */}
              <details className="mt-5 border-t border-slate-100 pt-4">
                <summary className="cursor-pointer text-sm font-semibold text-cyan-800 hover:text-cyan-600">
                  View all class scores
                </summary>

                {item.class_scores && (
                  <div className="mt-5 space-y-4">
                    {Object.entries(item.class_scores).map(
                      ([label, score]) => (
                        <div key={label}>
                          <div className="mb-1 flex justify-between gap-3 text-xs">
                            <span className="font-medium text-slate-600">
                              {label} · {classNames[label] ?? label}
                            </span>

                            <span className="font-semibold text-slate-700">
                              {(score * 100).toFixed(2)}%
                            </span>
                          </div>

                          <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                            <div
                              className="h-full rounded-full bg-cyan-600"
                              style={{
                                width: `${Math.min(
                                  100,
                                  Math.max(0, score * 100),
                                )}%`,
                              }}
                            />
                          </div>
                        </div>
                      ),
                    )}
                  </div>
                )}
              </details>

              <p className="mt-4 break-all text-[10px] text-slate-400">
                Prediction ID: {item.prediction_id}
              </p>
            </article>
          ))}
        </div>
      )}

      {/* Pagination */}
      {!loading && !error && history && history.total_pages > 1 && (
        <div className="flex flex-col justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-4 sm:flex-row sm:items-center">
          <p className="text-sm text-slate-500">
            Page {history.page} of {history.total_pages} · {history.total} records
          </p>

          <div className="flex gap-2">
            <button
              onClick={() => setPage((current) => Math.max(1, current - 1))}
              disabled={page <= 1}
              className="flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <ArrowLeft size={16} />
              Previous
            </button>

            <button
              onClick={() =>
                setPage((current) =>
                  Math.min(history.total_pages, current + 1),
                )
              }
              disabled={page >= history.total_pages}
              className="flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Next
              <ArrowRight size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Disclaimer */}
      <div className="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-5">
        <ShieldCheck className="mt-0.5 shrink-0 text-amber-700" size={20} />

        <div>
          <h4 className="text-sm font-bold text-amber-900">
            Research-only information
          </h4>

          <p className="mt-2 text-xs leading-5 text-amber-800">
            {history?.disclaimer ??
              "Experimental model predictions are not clinically validated and must not be used for diagnosis or treatment decisions."}
          </p>
        </div>
      </div>
    </section>
  );
}