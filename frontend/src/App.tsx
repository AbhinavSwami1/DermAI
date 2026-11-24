import { useEffect, useState } from "react";
import Login from "./components/Login";
import PredictionHistory from "./components/PredictionHistory";
import ReportActions from "./components/ReportActions";
import NotificationBell from "./components/NotificationBell";
import ProcessedImage from "./components/ProcessedImage";
import CompareAnalyses from "./components/CompareAnalyses";
import StaffDashboard from "./components/StaffDashboard";
import UsersAdmin from "./components/UsersAdmin";
import ModelInsights from "./components/ModelInsights";

import {
  apiRequest,
  apiRequestBlob,
  refreshAccessToken,
  setAccessToken,
} from "./api/client";

import {
  ChartNoAxesCombined,
  Clock3,
  History,
  LayoutDashboard,
  Microscope,
  ShieldCheck,
  Users,
} from "lucide-react";

type ImageQuality = {
  image_id: string;
  blur_score: number;
  brightness_mean: number;
  dark_pixel_percentage: number;
  bright_pixel_percentage: number;
  quality_status: string;
  quality_flags: string[];
  algorithm_version: string;
  assessed_at: string;
  disclaimer: string;
};

type ActiveView = "dashboard" | "history" | "insights" | "compare" | "staff" | "users";

const navigation = [
  { label: "Overview", icon: LayoutDashboard, view: "dashboard" },
  { label: "New Analysis", icon: Microscope, view: "dashboard" },
  { label: "Analysis History", icon: History, view: "history" },
  { label: "Compare Analyses", icon: Clock3, view: "compare" },
  { label: "Dashboards", icon: Users, view: "staff" },
  { label: "Users and Roles", icon: Users, view: "users" },
  {
    label: "Research Insights",
    icon: ChartNoAxesCombined,
    view: "insights",
  },
] as const;

const pageTitles: Record<ActiveView, [string, string]> = {
  dashboard: ["Skin image analysis", "Upload an image to receive a model prediction."],
  history: ["Analysis history", "Saved analyses, newest first."],
  compare: ["Compare analyses", "Two saved analyses side by side."],
  staff: ["Dashboards", "Aggregate figures for authorised roles."],
  users: ["Users and roles", "Assign or remove roles. Administrators only."],
  insights: ["Research insights", "Saved evaluation results for the deployed model."],
};


const conditions = [
  { code: "ACK", name: "Actinic Keratosis", count: 845 },
  { code: "BCC", name: "Basal Cell Carcinoma", count: 730 },
  { code: "NEV", name: "Melanocytic Nevus", count: 244 },
  { code: "SEK", name: "Seborrheic Keratosis", count: 235 },
  { code: "SCC", name: "Squamous Cell Carcinoma", count: 192 },
  { code: "MEL", name: "Melanoma", count: 52 },
];

function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [checkingSession, setCheckingSession] = useState(true);
  const [loggingOut, setLoggingOut] = useState(false);

  const [activeView, setActiveView] = useState<ActiveView>("dashboard");
  const [currentUser, setCurrentUser] = useState<{ full_name: string; email: string } | null>(null);
  const [totalAnalyses, setTotalAnalyses] = useState<number | null>(null);
  const [insights, setInsights] = useState<any>(null);
  const [roles, setRoles] = useState<string[]>([]);
  const isAdmin = roles.includes("Administrator");
  const hasStaffView =
    isAdmin || roles.some((r) => ["Dermatologist", "Medical Researcher", "Data Scientist"].includes(r));
  const visibleNavigation = navigation.filter((item) =>
    item.view === "staff" || item.view === "insights" ? hasStaffView : item.view === "users" ? isAdmin : true,
  );

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [pendingImageId, setPendingImageId] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [gradcamError, setGradcamError] = useState("");

  const [prediction, setPrediction] = useState<any>(null);
  const [imageQuality, setImageQuality] =
    useState<ImageQuality | null>(null);
  const [gradcamUrl, setGradcamUrl] = useState<string | null>(null);

  // Restore existing session
  useEffect(() => {
    let mounted = true;

    async function restoreSession() {
      try {
        const success = await refreshAccessToken();

        if (mounted) {
          setAuthenticated(success);
        }
      } catch (error) {
        console.error("Session restoration failed:", error);

        if (mounted) {
          setAccessToken(null);
          setAuthenticated(false);
        }
      } finally {
        if (mounted) {
          setCheckingSession(false);
        }
      }
    }

    restoreSession();

    return () => {
      mounted = false;
    };
  }, []);

  // Release temporary image URLs when the component unmounts
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      if (gradcamUrl) URL.revokeObjectURL(gradcamUrl);
    };
  }, [previewUrl, gradcamUrl]);

  // Load real values for the dashboard
  useEffect(() => {
    if (!authenticated) return;
    apiRequest<{ full_name: string; email: string }>("/users/me").then(setCurrentUser).catch(() => {});
    apiRequest<{ total: number }>("/predictions/history?page=1&page_size=1").then((d) => setTotalAnalyses(d.total)).catch(() => {});
    apiRequest<any>("/roles/me").then((r) => setRoles(r.roles)).catch(() => {});
    apiRequest<any>("/insights/model-info")
      .then((info) => {
        setInsights((prev: any) => ({ ...prev, ...info }));
        apiRequest<any>("/insights/model-metrics")
          .then((m) => setInsights((prev: any) => ({ ...prev, ...m })))
          .catch(() => {});
      })
      .catch(() => {});
  }, [authenticated, prediction]);

  const testAcc = insights?.test_metrics?.accuracy ?? insights?.test_metrics?.test_accuracy;
  const researchStats = [
    { label: "Your Analyses", value: totalAnalyses ?? "-", change: "Saved in your history" },
    { label: "Test Accuracy", value: typeof testAcc === "number" ? (testAcc <= 1 ? (testAcc * 100).toFixed(2) + "%" : String(testAcc)) : "Not available", change: "Held-out test set (saved evaluation)" },
    { label: "Supported Classes", value: insights?.num_classes ?? "-", change: (insights?.class_names ?? []).join(", ") },
    { label: "Model Version", value: insights?.model_version ?? "-", change: "Currently deployed model" },
  ];

  // Navigation handler
  function handleNavigation(view: ActiveView, label?: string) {
    setActiveView(view);

    if (label === "New Analysis") {
      window.setTimeout(() => {
        document
          .getElementById("new-analysis")
          ?.scrollIntoView({ behavior: "smooth", block: "center" });
      }, 100);
    }
  }

  // Image selection
  function handleFileSelection(
    event: React.ChangeEvent<HTMLInputElement>,
  ) {
    const file = event.target.files?.[0];

    if (!file) return;

    setPendingImageId(null);

    if (!["image/jpeg", "image/png"].includes(file.type)) {
      setUploadError("Please select a JPG or PNG image.");
      event.target.value = "";
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setUploadError("Image size must not exceed 10 MB.");
      event.target.value = "";
      return;
    }

    if (previewUrl) URL.revokeObjectURL(previewUrl);
    if (gradcamUrl) URL.revokeObjectURL(gradcamUrl);

    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));

    setPrediction(null);
setGradcamUrl(null);
setImageQuality(null);
setUploadError("");
setGradcamError("");

    event.target.value = "";
  }

  // Prediction + Grad-CAM stage for an already uploaded image
  async function runPrediction(imageId: string, acknowledge: boolean) {
    setPendingImageId(null);
    setProcessing(true);
    setUploadError("");
    setGradcamError("");
    try {
    // Step 4: Run experimental prediction
    const predictionResult = await apiRequest<{
      prediction_id: string;
      predicted_label: string;
      confidence: number;
      class_scores: Record<string, number>;
      model_version: string;
      status: string;
      disclaimer: string;
    }>(`/predictions/${imageId}?acknowledge_quality_warning=${acknowledge}`, {
      method: "POST",
    });

    // Preserve successful prediction independently
    setPrediction(predictionResult);

    // Step 5: Generate Grad-CAM independently
    try {
      const gradcamBlob = await apiRequestBlob(
        `/predictions/${imageId}/gradcam?acknowledge_quality_warning=${acknowledge}`,
      );

      setGradcamUrl(URL.createObjectURL(gradcamBlob));
    } catch (error) {
      console.error("Grad-CAM generation failed:", error);

      setGradcamError(
        error instanceof Error
          ? error.message
          : "Prediction succeeded, but Grad-CAM visualization could not be generated.",
      );
    }
    } catch (error) {
      console.error("Prediction failed:", error);
      setUploadError(
        error instanceof Error ? error.message : "Prediction failed.",
      );
    } finally {
      setProcessing(false);
    }
  }

  // Complete image analysis workflow
async function handleAnalyze() {
  if (!selectedFile || processing) return;

  setProcessing(true);
  setUploadError("");
  setGradcamError("");
  setPrediction(null);
  setImageQuality(null);

  if (gradcamUrl) {
    URL.revokeObjectURL(gradcamUrl);
    setGradcamUrl(null);
  }

  try {
    // Step 1: Create research case
    const newCase = await apiRequest<{ case_id: string }>("/cases", {
      method: "POST",
    });

    // Step 2: Upload image
    const formData = new FormData();
    formData.append("case_id", newCase.case_id);
    formData.append("file", selectedFile);

    const uploadedImage = await apiRequest<{
      image_id: string;
      original_filename: string;
    }>("/upload", {
      method: "POST",
      body: formData,
    });

    // Step 3: Fetch image quality assessment
    const qualityResult = await apiRequest<ImageQuality>(
      `/images/${uploadedImage.image_id}/quality`,
    );

    setImageQuality(qualityResult);

    // Step 4: a quality WARNING needs explicit user confirmation
    if (qualityResult.quality_status === "WARNING") {
      setPendingImageId(uploadedImage.image_id);
      return;
    }

    await runPrediction(uploadedImage.image_id, false);
  } catch (error) {
    console.error("Image analysis failed:", error);

    setUploadError(
      error instanceof Error
        ? error.message
        : "Something went wrong during image analysis.",
    );
  } finally {
    setProcessing(false);
  }
}

  // Logout and revoke refresh token
  async function handleLogout() {
    if (loggingOut) return;

    setLoggingOut(true);

    try {
      await apiRequest("/auth/logout", {
        method: "POST",
      });
    } catch (error) {
      console.error("Logout request failed:", error);
    } finally {
      setAccessToken(null);
      setAuthenticated(false);
      setLoggingOut(false);
    }
  }

  // Session restoration screen
  if (checkingSession) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-stone-100">
        <div className="text-center">
          <h2 className="text-lg font-bold text-slate-900">
            DermAI
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            Restoring your research session...
          </p>
        </div>
      </div>
    );
  }

  // Login screen
  if (!authenticated) {
    return (
      <Login onLoginSuccess={() => setAuthenticated(true)} />
    );
  }

  return (
    <div className="min-h-screen bg-stone-100">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center gap-6 px-5 sm:px-8">
          <span className="py-4 font-serif text-xl font-semibold text-slate-900">DermAI</span>
          <nav className="flex flex-1 gap-1 overflow-x-auto" aria-label="Main">
            {visibleNavigation.map(({ label, view }) => {
              const isActive = label === "New Analysis" ? false : activeView === view;
              return (
                <button
                  key={label}
                  onClick={() => handleNavigation(view as ActiveView, label)}
                  className={`whitespace-nowrap border-b-2 px-3 py-4 text-sm ${
                    isActive
                      ? "border-cyan-700 font-semibold text-slate-900"
                      : "border-transparent text-slate-500 hover:text-slate-900"
                  }`}
                >
                  {label}
                </button>
              );
            })}
          </nav>
          <div className="flex items-center gap-3 py-2">
            <NotificationBell refreshKey={prediction?.prediction_id} />
            <span className="hidden text-sm text-slate-600 md:inline">{currentUser?.full_name ?? ""}{roles.length ? ` (${roles.join(", ")})` : ""}</span>
            <button
              onClick={handleLogout}
              disabled={loggingOut}
              className="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loggingOut ? "Logging out..." : "Log out"}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="min-w-0">
        {/* Page title */}
        <div className="border-b border-slate-200 bg-white">
          <div className="mx-auto max-w-6xl px-5 py-6 sm:px-8">
            <h1 className="text-2xl font-semibold text-slate-900">{pageTitles[activeView][0]}</h1>
            <p className="mt-1 text-sm text-slate-500">{pageTitles[activeView][1]}</p>
          </div>
        </div>

        <div className="mx-auto max-w-6xl space-y-8 px-5 py-8 sm:px-8">
          {/* Analysis History */}
          {activeView === "history" && <PredictionHistory />}

          {activeView === "compare" && <CompareAnalyses />}
          {activeView === "staff" && <StaffDashboard />}
          {activeView === "users" && <UsersAdmin />}
          {activeView === "insights" && <ModelInsights />}

          {/* Dashboard */}
          {activeView === "dashboard" && (
            <>
              {/* Summary */}
              <section
                aria-label="Summary"
                className="grid gap-px overflow-hidden rounded-md border border-slate-200 bg-slate-200 sm:grid-cols-2 xl:grid-cols-4"
              >
                {researchStats.filter((st) => st.label !== "Test Accuracy" || typeof testAcc === "number").map(({ label, value, change }) => (
                  <div key={label} className="bg-white p-5">
                    <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
                    <p className="mt-2 break-words font-serif text-xl font-semibold text-slate-900">{value}</p>
                    <p className="mt-1 text-xs text-slate-500">{change}</p>
                  </div>
                ))}
              </section>

              {/* Analysis and Model Information */}
              <section className="grid gap-6 xl:grid-cols-5">
                {/* Image Analysis */}
                <div
                  id="new-analysis"
                  className="rounded-md border border-slate-200/70 bg-white p-6  xl:col-span-3"
                >
                  <div className="mb-6">
                    <h3 className="text-xl font-semibold text-slate-900">Analyze an image</h3>
                    <p className="mt-1 text-sm text-slate-500">
                      Upload a JPEG or PNG photo of the skin area. The image is checked for
                      quality before the model runs.
                    </p>
                  </div>

                  <div className="flex min-h-64 flex-col items-center justify-center rounded-md border border-dashed border-slate-300 bg-slate-50 px-5 py-6 text-center">
                    {!previewUrl ? (
                      <>

                        <h4 className="font-semibold text-slate-800">
                          No image selected
                        </h4>

                        <p className="mt-2 max-w-sm text-xs leading-5 text-slate-500">
                          Use a clear, well-lit close-up of the skin area.
                        </p>
                      </>
                    ) : (
                      <>
                        <img
                          src={previewUrl}
                          alt="Selected research image preview"
                          className="mb-4 max-h-64 max-w-full rounded object-contain "
                        />

                        <p className="max-w-full break-all text-sm font-medium text-slate-700">
                          {selectedFile?.name}
                        </p>
                      </>
                    )}

                    <div className="mt-5 flex flex-wrap justify-center gap-3">
                      <label className="cursor-pointer rounded bg-white px-5 py-3 text-sm font-semibold text-cyan-700  transition hover:bg-cyan-100">
                      {previewUrl
                        ? "Choose a different image"
                        : "Choose image"}

                      <input
                        type="file"
                        accept="image/jpeg,image/png"
                        className="hidden"
                        disabled={processing}
                        onChange={handleFileSelection}
                      />
                    </label>
                      <label className="cursor-pointer rounded bg-white px-5 py-3 text-sm font-semibold text-cyan-700  transition hover:bg-cyan-100">
                      Take photo

                      <input
                        type="file"
                        capture="environment"
                        accept="image/jpeg,image/png"
                        className="hidden"
                        disabled={processing}
                        onChange={handleFileSelection}
                      />
                    </label>
                    </div>
                    <p className="mt-2 text-xs text-slate-500">On a phone, Take photo opens the camera.</p>

                    {selectedFile && (
                      <button
                        onClick={handleAnalyze}
                        disabled={processing}
                        className="mt-3 rounded bg-cyan-700 px-6 py-3 text-sm font-semibold text-white  transition hover:bg-cyan-800 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {processing
                          ? "Analyzing..."
                          : "Analyze image"}
                      </button>
                    )}

                    {pendingImageId && (
                      <div className="mt-4 rounded border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                        <p className="font-semibold">Image quality warning</p>
                        <p className="mt-1">
                          This image may be blurry or have low texture. Predictions on such
                          images may be less reliable. Continue with this image, or choose a clearer one.
                        </p>
                        <div className="mt-3 flex flex-wrap gap-3">
                          <button
                            onClick={() => runPrediction(pendingImageId, true)}
                            disabled={processing}
                            className="rounded-md bg-cyan-700 px-4 py-2 text-xs font-semibold text-white hover:bg-cyan-800 disabled:opacity-60"
                          >
                            Continue anyway
                          </button>
                          <button
                            onClick={() => setPendingImageId(null)}
                            className="rounded-md border border-amber-300 px-4 py-2 text-xs font-semibold text-amber-900 hover:bg-amber-100"
                          >
                            Choose another image
                          </button>
                        </div>
                      </div>
                    )}

                    {uploadError && (
                      <p className="mt-4 text-sm font-medium text-red-600">
                        {uploadError}
                      </p>
                    )}

                    {/* Image Quality Assessment */}
                    {imageQuality && (
                      <div className="mt-6 w-full rounded border border-slate-200 bg-slate-50 p-5 text-left">
                        <div className="flex flex-wrap items-center justify-between gap-3">
                          <div>
                            <h4 className="font-bold text-slate-900">
                              Image Quality Assessment
                            </h4>

                            <p className="mt-1 text-xs text-slate-500">
                              Automated image quality analysis
                            </p>
                          </div>

                          <span
                            className={`rounded-full px-3 py-1.5 text-xs font-bold ${
                              imageQuality.quality_status ===
                              "ACCEPTABLE"
                                ? "bg-emerald-100 text-emerald-700"
                                : "bg-amber-100 text-amber-800"
                            }`}
                          >
                            {imageQuality.quality_status.replaceAll(
                              "_",
                              " ",
                            )}
                          </span>
                        </div>

                        <div className="mt-5 grid grid-cols-2 gap-3">
                          {[
                            {
                              label: "Blur Score",
                              value: imageQuality.blur_score.toFixed(2),
                            },
                            {
                              label: "Brightness Mean",
                              value:
                                imageQuality.brightness_mean.toFixed(2),
                            },
                            {
                              label: "Dark Pixels",
                              value: `${imageQuality.dark_pixel_percentage.toFixed(2)}%`,
                            },
                            {
                              label: "Bright Pixels",
                              value: `${imageQuality.bright_pixel_percentage.toFixed(2)}%`,
                            },
                          ].map((metric) => (
                            <div
                              key={metric.label}
                              className="rounded-md border border-slate-200 bg-white p-3"
                            >
                              <p className="text-xs text-slate-500">
                                {metric.label}
                              </p>

                              <p className="mt-2 text-lg font-bold text-slate-800">
                                {metric.value}
                              </p>
                            </div>
                          ))}
                        </div>

                        <div className="mt-5">
                          <h5 className="text-sm font-semibold text-slate-800">
                            Quality Flags
                          </h5>

                          {imageQuality.quality_flags.length > 0 ? (
                            <div className="mt-2 flex flex-wrap gap-2">
                              {imageQuality.quality_flags.map((flag) => (
                                <span
                                  key={flag}
                                  className="rounded-md bg-amber-100 px-3 py-1.5 text-xs font-medium text-amber-800"
                                >
                                  {flag.replaceAll("_", " ")}
                                </span>
                              ))}
                            </div>
                          ) : (
                            <p className="mt-2 text-xs text-emerald-700">
                              No quality flags detected by the current
                              assessment.
                            </p>
                          )}
                        </div>

                        <p className="mt-4 text-[11px] text-slate-400">
                          Assessment algorithm version:{" "}
                          {imageQuality.algorithm_version}
                        </p>

                        <p className="mt-3 rounded-md bg-amber-50 p-3 text-xs leading-5 text-amber-800">
                          {imageQuality.disclaimer}
                        </p>
                      </div>
                    )}

                    {/* Experimental Prediction */}
                    {prediction && (
                      <div className="mt-6 w-full rounded border border-cyan-100 bg-white p-5 text-left">
                        <h4 className="font-bold text-slate-900">
                          Model prediction (experimental)
                        </h4>

                        <p className="mt-3 text-lg font-bold text-cyan-700">
                          {prediction.predicted_label}
                        </p>

                        <p className="mt-1 text-sm text-slate-600">
                          Confidence:{" "}
                          {(prediction.confidence * 100).toFixed(2)}%
                        </p>

                        <p className="mt-1 text-xs text-slate-500">
                          Model: {prediction.model_version}
                        </p>

                        <h5 className="mt-5 text-sm font-semibold text-slate-800">
                          Class-wise Scores
                        </h5>

                        <div className="mt-3 space-y-3">
                          {Object.entries(
                            prediction.class_scores,
                          ).map(([label, score]) => (
                            <div key={label}>
                              <div className="mb-1 flex justify-between text-xs text-slate-600">
                                <span>{label}</span>
                                <span>
                                  {(Number(score) * 100).toFixed(2)}%
                                </span>
                              </div>

                              <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                                <div
                                  className="h-full rounded-full bg-cyan-600"
                                  style={{
                                    width: `${Number(score) * 100}%`,
                                  }}
                                />
                              </div>
                            </div>
                          ))}
                        </div>

                        {Array.isArray(prediction.top_predictions) && (
                          <div className="mt-5">
                            <h5 className="text-sm font-semibold text-slate-800">
                              Top-3 predictions
                            </h5>
                            <ol className="mt-2 space-y-1 text-sm text-slate-700">
                              {prediction.top_predictions.map(
                                (t: { rank: number; class_name: string; score: number }) => (
                                  <li key={t.rank}>
                                    {t.class_name} ({(t.score * 100).toFixed(2)}%)
                                  </li>
                                ),
                              )}
                            </ol>
                          </div>
                        )}
                        <p className="mt-3 text-xs text-slate-500">
                          Analysis time: {new Date(prediction.created_at).toLocaleString()}
                        </p>
                        <p className="mt-1 text-xs text-slate-500">
                          Scores are model outputs, not clinically validated probabilities.
                        </p>
                        <ReportActions predictionId={prediction.prediction_id} />

                        <ProcessedImage key={prediction.prediction_id} imageId={prediction.image_id} />

                        {/* Grad-CAM */}
                        {gradcamUrl && (
                          <div className="mt-6">
                            <h5 className="mb-3 text-sm font-semibold text-slate-800">
                              Grad-CAM Research Visualization
                            </h5>

                            <img
                              src={gradcamUrl}
                              alt="Grad-CAM attention visualization"
                              className="w-full rounded border border-slate-200"
                            />
                          </div>
                        )}
                        {gradcamError && (
  <p className="mt-4 rounded-md bg-amber-50 p-3 text-sm text-amber-800">
    Prediction completed successfully, but Grad-CAM visualization
    is unavailable: {gradcamError}
  </p>
)}

                        <p className="mt-5 rounded-md bg-amber-50 p-3 text-xs leading-5 text-amber-800">
                          Research prototype output only. This
                          prediction and Grad-CAM visualization are
                          not medical diagnoses and must not be used
                          for clinical decisions.
                        </p>
                      </div>
                    )}

                    <p className="mt-4 text-[11px] text-slate-400">
                      Research prototype · JPG / PNG · Maximum 10 MB
                    </p>
                  </div>
                </div>

                {/* Model Information */}
                <div className="rounded-md border border-slate-200/70 bg-white p-6  xl:col-span-2">
                  <div className="mb-6 flex items-center justify-between">
                    <div>
                      <h3 className="font-bold text-slate-900">
                        Model Information
                      </h3>

                      <p className="mt-1 text-xs text-slate-400">
                        Current research baseline
                      </p>
                    </div>
                  </div>

                  <div className="space-y-5">
                    {[
  ["Architecture", "MobileNetV3-Large"],
  ["Version", "Fine-tuned Epoch 9"],
  ["Input Size", "224 × 224 pixels"],
  ["Classes", "6 skin conditions"],
  ["Normalization", "ImageNet Mean / Std"],
  ["Device", "Auto-detected"],
].map(([key, value]) => (
                      <div
                        key={key}
                        className="flex items-center justify-between gap-3 border-b border-slate-100 pb-3"
                      >
                        <span className="text-sm text-slate-500">
                          {key}
                        </span>

                        <span className="text-right text-sm font-semibold text-slate-800">
                          {value}
                        </span>
                      </div>
                    ))}
                  </div>

                  <div className="mt-5 flex items-center gap-2 rounded bg-amber-50 p-3 text-xs leading-5 text-amber-800">
                    <ShieldCheck size={18} className="shrink-0" />
                    Experimental model. Not clinically validated.
                  </div>
                </div>
              </section>

              {/* Dataset Distribution */}
              <section className="rounded-md border border-slate-200/70 bg-white p-6 ">
                <div className="mb-6 flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
                  <div>
                    <h3 className="text-lg font-bold text-slate-900">
                      Dataset class distribution
                    </h3>

                    <p className="mt-1 text-xs text-slate-400">
                      PAD-UFES-20 dataset audit (static reference)
                    </p>
                  </div>

                  <span className="rounded-md bg-cyan-50 px-3 py-2 text-xs font-semibold text-cyan-700">
                    6 condition classes
                  </span>
                </div>

                <div className="grid gap-x-8 gap-y-5 md:grid-cols-2">
                  {conditions.map(({ code, name, count }) => (
                    <div key={code}>
                      <div className="mb-2 flex items-center justify-between gap-3 text-sm">
                        <span className="font-semibold text-slate-700">
                          {code}{" "}
                          <span className="font-normal text-slate-500">
                            · {name}
                          </span>
                        </span>

                        <span className="font-semibold text-slate-700">
                          {count}
                        </span>
                      </div>

                      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full bg-cyan-500"
                          style={{
                            width: `${(count / 845) * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              {/* Footer */}
              <footer className="flex flex-col gap-2 border-t border-slate-200 py-5 text-xs leading-5 text-slate-400 sm:flex-row sm:items-center sm:justify-between">
                <span>
                  © 2026 DermAI · Academic Research Prototype
                </span>

                <span className="flex items-center gap-2">
                  <Clock3 size={14} />
                  Model results are experimental and not for clinical use.
                </span>
              </footer>
            </>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;