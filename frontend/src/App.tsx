import { useEffect, useState } from "react";
import Login from "./components/Login";
import PredictionHistory from "./components/PredictionHistory";

import {
  apiRequest,
  apiRequestBlob,
  refreshAccessToken,
  setAccessToken,
} from "./api/client";

import {
  Activity,
  ArrowRight,
  Bell,
  BrainCircuit,
  ChartNoAxesCombined,
  ChevronDown,
  CircleHelp,
  Clock3,
  FileImage,
  FlaskConical,
  History,
  LayoutDashboard,
  LogOut,
  Microscope,
  Settings,
  ShieldCheck,
  Sparkles,
  Upload,
  UserRound,
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

type ActiveView = "dashboard" | "history" | "insights";

const navigation = [
  { label: "Dashboard", icon: LayoutDashboard, view: "dashboard" },
  { label: "New Analysis", icon: Microscope, view: "dashboard" },
  { label: "Analysis History", icon: History, view: "history" },
  {
    label: "Research Insights",
    icon: ChartNoAxesCombined,
    view: "insights",
  },
] as const;

const researchStats = [
  {
    label: "Total Images",
    value: "2,298",
    change: "PAD-UFES-20 dataset",
    icon: FileImage,
  },
  {
    label: "Model Accuracy",
    value: "55.0%",
    change: "Baseline test accuracy",
    icon: BrainCircuit,
  },
  {
    label: "Skin Conditions",
    value: "06",
    change: "Supported classes",
    icon: Activity,
  },
  {
    label: "Model Version",
    value: "1.0.0",
    change: "MobileNetV3-Small",
    icon: FlaskConical,
  },
];

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

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [uploadError, setUploadError] = useState("");

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

    event.target.value = "";
  }

  // Complete image analysis workflow
  async function handleAnalyze() {
    if (!selectedFile || processing) return;

    setProcessing(true);
    setUploadError("");
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

      // Step 4: Run experimental prediction
      const predictionResult = await apiRequest<{
        prediction_id: string;
        predicted_label: string;
        confidence: number;
        class_scores: Record<string, number>;
        model_version: string;
        status: string;
        disclaimer: string;
      }>(`/predictions/${uploadedImage.image_id}`, {
        method: "POST",
      });

      setPrediction(predictionResult);

      // Step 5: Generate Grad-CAM visualization
      const gradcamBlob = await apiRequestBlob(
        `/predictions/${uploadedImage.image_id}/gradcam`,
      );

      setGradcamUrl(URL.createObjectURL(gradcamBlob));
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
      <div className="flex min-h-screen items-center justify-center bg-[#f5f7fb]">
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
    <div className="min-h-screen bg-[#f5f7fb]">
      {/* Sidebar */}
      <aside className="flex w-full flex-col border-r border-slate-200 bg-white text-slate-800 lg:fixed lg:inset-y-0 lg:w-64">
        <div className="flex items-center gap-3 border-b border-slate-100 px-7 py-7">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-400 text-[#101d35]">
            <Microscope size={25} />
          </div>

          <div>
            <h1 className="text-xl font-bold tracking-wide text-slate-900">
              DermAI
            </h1>
            <p className="text-xs text-slate-500">
              Research Platform
            </p>
          </div>
        </div>

        <div className="px-5 pt-8">
          <p className="mb-4 px-3 text-[10px] font-bold uppercase tracking-[2px] text-slate-500">
            Workspace
          </p>

          <nav className="space-y-2">
            {navigation.map(({ label, icon: Icon, view }) => {
              const isActive =
                label === "New Analysis"
                  ? false
                  : activeView === view;

              return (
                <button
                  key={label}
                  onClick={() =>
                    handleNavigation(view as ActiveView, label)
                  }
                  className={`flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm transition ${
                    isActive
                      ? "bg-cyan-50 font-semibold text-cyan-800 ring-1 ring-cyan-100"
                      : "text-slate-500 hover:bg-slate-100 hover:text-slate-900"
                  }`}
                >
                  <Icon size={19} />
                  {label}
                </button>
              );
            })}
          </nav>
        </div>

        <div className="px-5 pt-9">
          <p className="mb-4 px-3 text-[10px] font-bold uppercase tracking-[2px] text-slate-500">
            Management
          </p>

          <nav className="space-y-2">
            <button
              disabled
              className="flex w-full cursor-not-allowed items-center gap-3 rounded-xl px-4 py-3 text-sm text-slate-400"
            >
              <Users size={19} />
              Research Team
            </button>

            <button
              disabled
              className="flex w-full cursor-not-allowed items-center gap-3 rounded-xl px-4 py-3 text-sm text-slate-400"
            >
              <Settings size={19} />
              Settings
            </button>

            <button
              disabled
              className="flex w-full cursor-not-allowed items-center gap-3 rounded-xl px-4 py-3 text-sm text-slate-400"
            >
              <CircleHelp size={19} />
              Help & Support
            </button>
          </nav>
        </div>

        <div className="mt-auto hidden p-5 lg:block">
          <div className="rounded-2xl border border-cyan-100 bg-cyan-50/70 p-4">
            <div className="mb-3 flex items-center gap-2 text-cyan-700">
              <ShieldCheck size={18} />
              <span className="text-xs font-semibold">
                Research Mode
              </span>
            </div>

            <p className="text-xs leading-5 text-slate-600">
              Experimental AI research platform. Not intended for
              clinical diagnosis.
            </p>
          </div>

          <div className="mt-5 flex items-center gap-3 border-t border-slate-100 pt-5">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-cyan-400/15 text-cyan-700">
              <UserRound size={20} />
            </div>

            <div>
              <p className="text-sm font-semibold">Researcher</p>
              <p className="text-xs text-slate-500">
                Research Workspace
              </p>
            </div>

            <ChevronDown
              className="ml-auto text-slate-500"
              size={17}
            />
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="min-w-0 flex-1 lg:ml-64">
        {/* Header */}
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-5 py-5 sm:px-9">
          <div>
            <p className="text-xs font-medium text-slate-400">
              RESEARCH WORKSPACE / {activeView.toUpperCase()}
            </p>

            <h2 className="mt-1 text-xl font-bold text-slate-900">
              {activeView === "history"
                ? "Analysis History"
                : activeView === "insights"
                  ? "Research Insights"
                  : "Dashboard"}
            </h2>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleLogout}
              disabled={loggingOut}
              className="flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-600 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <LogOut size={17} />
              <span className="hidden sm:inline">
                {loggingOut ? "Logging out..." : "Logout"}
              </span>
            </button>

            <button
              type="button"
              aria-label="Notifications"
              className="relative rounded-xl border border-slate-200 p-3 text-slate-500 hover:bg-slate-50"
            >
              <Bell size={19} />
              <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-cyan-500" />
            </button>
          </div>
        </header>

        <div className="mx-auto max-w-7xl space-y-8 p-5 sm:p-9">
          {/* Analysis History */}
          {activeView === "history" && <PredictionHistory />}

          {/* Research Insights */}
          {activeView === "insights" && (
            <section className="rounded-2xl border border-slate-200 bg-white p-8">
              <div className="flex items-center gap-3">
                <ChartNoAxesCombined
                  className="text-cyan-700"
                  size={25}
                />
                <h2 className="text-xl font-bold text-slate-900">
                  Research Insights
                </h2>
              </div>

              <p className="mt-3 text-sm leading-6 text-slate-500">
                The research insights dashboard is planned for a
                later development phase.
              </p>
            </section>
          )}

          {/* Dashboard */}
          {activeView === "dashboard" && (
            <>
              {/* Welcome */}
              <section className="flex flex-col justify-between gap-5 sm:flex-row sm:items-center">
                <div>
                  <p className="text-sm text-slate-500">
                    Welcome to your research workspace
                  </p>

                  <h2 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
                    Skin Lesion Analysis
                  </h2>

                  <p className="mt-2 text-sm text-slate-500">
                    Explore experimental deep learning research
                    and model insights.
                  </p>
                </div>

                <button
                  onClick={() => handleNavigation("dashboard", "New Analysis")}
                  className="flex items-center justify-center gap-2 rounded-xl bg-[#0f766e] px-5 py-3 text-sm font-semibold text-white shadow-lg transition hover:bg-[#115e59]"
                >
                  <Upload size={17} />
                  New Analysis
                  <ArrowRight size={16} />
                </button>
              </section>

              {/* Statistics */}
              <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                {researchStats.map(
                  ({ label, value, change, icon: Icon }) => (
                    <div
                      key={label}
                      className="rounded-2xl border border-slate-200/70 bg-white p-5 shadow-[0_2px_8px_rgba(15,23,42,0.04)] transition-shadow hover:shadow-md"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-slate-500">
                          {label}
                        </span>

                        <div className="rounded-xl bg-cyan-50 p-2.5 text-cyan-700">
                          <Icon size={20} />
                        </div>
                      </div>

                      <p className="mt-5 text-3xl font-bold tracking-tight text-slate-900">
                        {value}
                      </p>

                      <p className="mt-2 text-xs text-slate-400">
                        {change}
                      </p>
                    </div>
                  ),
                )}
              </section>

              {/* Analysis and Model Information */}
              <section className="grid gap-6 xl:grid-cols-5">
                {/* Image Analysis */}
                <div
                  id="new-analysis"
                  className="rounded-2xl border border-slate-200/70 bg-white p-6 shadow-[0_2px_10px_rgba(15,23,42,0.04)] xl:col-span-3"
                >
                  <div className="mb-6">
                    <div className="flex items-center gap-2 text-cyan-700">
                      <Sparkles size={19} />
                      <span className="text-xs font-bold uppercase tracking-wider">
                        AI Analysis
                      </span>
                    </div>

                    <h3 className="mt-2 text-xl font-bold text-slate-900">
                      Start a new analysis
                    </h3>

                    <p className="mt-1 text-sm text-slate-500">
                      Upload a skin lesion image to explore model
                      predictions.
                    </p>
                  </div>

                  <div className="flex min-h-64 flex-col items-center justify-center rounded-2xl border-2 border-dashed border-cyan-200 bg-cyan-50/40 px-5 py-6 text-center">
                    {!previewUrl ? (
                      <>
                        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-white text-cyan-600 shadow-sm">
                          <Upload size={29} />
                        </div>

                        <h4 className="font-semibold text-slate-800">
                          Upload your research image
                        </h4>

                        <p className="mt-2 max-w-sm text-xs leading-5 text-slate-500">
                          Select a JPG or PNG image from the
                          PAD-UFES-20 or Fitzpatrick17k research
                          datasets.
                        </p>
                      </>
                    ) : (
                      <>
                        <img
                          src={previewUrl}
                          alt="Selected research image preview"
                          className="mb-4 max-h-64 max-w-full rounded-xl object-contain shadow-sm"
                        />

                        <p className="max-w-full break-all text-sm font-medium text-slate-700">
                          {selectedFile?.name}
                        </p>
                      </>
                    )}

                    <label className="mt-5 cursor-pointer rounded-xl bg-white px-5 py-3 text-sm font-semibold text-cyan-700 shadow-sm transition hover:bg-cyan-100">
                      {previewUrl
                        ? "Choose Another Image"
                        : "Select Research Image"}

                      <input
                        type="file"
                        accept="image/jpeg,image/png"
                        className="hidden"
                        disabled={processing}
                        onChange={handleFileSelection}
                      />
                    </label>

                    {selectedFile && (
                      <button
                        onClick={handleAnalyze}
                        disabled={processing}
                        className="mt-3 rounded-xl bg-[#0f766e] px-6 py-3 text-sm font-semibold text-white shadow-md transition hover:bg-[#115e59] disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {processing
                          ? "Analyzing Research Image..."
                          : "Run AI Analysis"}
                      </button>
                    )}

                    {uploadError && (
                      <p className="mt-4 text-sm font-medium text-red-600">
                        {uploadError}
                      </p>
                    )}

                    {/* Image Quality Assessment */}
                    {imageQuality && (
                      <div className="mt-6 w-full rounded-xl border border-slate-200 bg-slate-50 p-5 text-left">
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
                              className="rounded-lg border border-slate-200 bg-white p-3"
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
                                  className="rounded-lg bg-amber-100 px-3 py-1.5 text-xs font-medium text-amber-800"
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

                        <p className="mt-3 rounded-lg bg-amber-50 p-3 text-xs leading-5 text-amber-800">
                          {imageQuality.disclaimer}
                        </p>
                      </div>
                    )}

                    {/* Experimental Prediction */}
                    {prediction && (
                      <div className="mt-6 w-full rounded-xl border border-cyan-100 bg-white p-5 text-left">
                        <h4 className="font-bold text-slate-900">
                          Experimental Model Prediction
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

                        {/* Grad-CAM */}
                        {gradcamUrl && (
                          <div className="mt-6">
                            <h5 className="mb-3 text-sm font-semibold text-slate-800">
                              Grad-CAM Research Visualization
                            </h5>

                            <img
                              src={gradcamUrl}
                              alt="Grad-CAM attention visualization"
                              className="w-full rounded-xl border border-slate-200"
                            />
                          </div>
                        )}

                        <p className="mt-5 rounded-lg bg-amber-50 p-3 text-xs leading-5 text-amber-800">
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
                <div className="rounded-2xl border border-slate-200/70 bg-white p-6 shadow-[0_2px_10px_rgba(15,23,42,0.04)] xl:col-span-2">
                  <div className="mb-6 flex items-center justify-between">
                    <div>
                      <h3 className="font-bold text-slate-900">
                        Model Information
                      </h3>

                      <p className="mt-1 text-xs text-slate-400">
                        Current research baseline
                      </p>
                    </div>

                    <div className="rounded-xl bg-emerald-50 p-2.5 text-emerald-600">
                      <BrainCircuit size={21} />
                    </div>
                  </div>

                  <div className="space-y-5">
                    {[
                      ["Architecture", "MobileNetV3-Small"],
                      ["Version", "1.0.0-epoch20"],
                      ["Input Size", "224 × 224 pixels"],
                      ["Classes", "6 skin conditions"],
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

                  <div className="mt-5 flex items-center gap-2 rounded-xl bg-amber-50 p-3 text-xs leading-5 text-amber-800">
                    <ShieldCheck size={18} className="shrink-0" />
                    Experimental model. Not clinically validated.
                  </div>
                </div>
              </section>

              {/* Dataset Distribution */}
              <section className="rounded-2xl border border-slate-200/70 bg-white p-6 shadow-[0_2px_10px_rgba(15,23,42,0.04)]">
                <div className="mb-6 flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
                  <div>
                    <h3 className="text-lg font-bold text-slate-900">
                      Research Dataset Distribution
                    </h3>

                    <p className="mt-1 text-xs text-slate-400">
                      PAD-UFES-20 · 2,298 images
                    </p>
                  </div>

                  <span className="rounded-lg bg-cyan-50 px-3 py-2 text-xs font-semibold text-cyan-700">
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