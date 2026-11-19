import { ArrowRight, ShieldAlert } from "lucide-react";

interface LandingProps {
  onLogin: () => void;
  onRegister: () => void;
}

const steps = [
  { n: "1", title: "Upload image", text: "Select a JPEG or PNG photograph of a skin area." },
  { n: "2", title: "Image assessment", text: "The system checks resolution, focus and exposure before analysis." },
  { n: "3", title: "AI analysis", text: "A trained classifier returns a predicted class with model scores." },
  { n: "4", title: "Result review", text: "Review Top-3 predictions, the Grad-CAM view and export a report." },
];

const capabilities = [
  { title: "Image classification", text: "Six lesion categories from the PAD-UFES-20 dataset: ACK, BCC, MEL, NEV, SCC and SEK." },
  { title: "Confidence-aware output", text: "Each result shows the model score and the Top-3 alternatives. Scores are not clinical probabilities." },
  { title: "Explainability", text: "Grad-CAM highlights image regions that influenced the model. It is not lesion segmentation." },
  { title: "History and reports", text: "Every analysis is saved with its model version and can be reopened or exported as PDF, CSV or JSON." },
];

export default function Landing({ onLogin, onRegister }: LandingProps) {
  return (
    <div className="min-h-screen bg-white text-slate-900">
      <header className="border-b border-slate-200">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
          <span className="text-lg font-bold tracking-wide">DermAI</span>
          <nav className="flex items-center gap-3 text-sm">
            <button onClick={onLogin} className="rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100">
              Log in
            </button>
            <button onClick={onRegister} className="rounded-md bg-cyan-700 px-4 py-2 font-medium text-white hover:bg-cyan-800">
              Register
            </button>
          </nav>
        </div>
      </header>

      <main>
        <section className="mx-auto max-w-6xl px-5 py-16 sm:py-24">
          <p className="text-xs font-semibold uppercase tracking-widest text-cyan-700">
            Skin-image analysis research platform
          </p>
          <h1 className="mt-3 max-w-3xl text-3xl font-bold leading-tight sm:text-5xl">
            Analyse a skin photograph with a deep-learning classifier.
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-slate-600">
            DermAI checks image quality, runs a trained model, and shows the
            predicted condition with its scores and an explanation map. It is
            built as decision support for screening and research.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <button onClick={onRegister} className="inline-flex items-center gap-2 rounded-md bg-cyan-700 px-5 py-3 text-sm font-semibold text-white hover:bg-cyan-800">
              Start skin-image analysis <ArrowRight size={16} />
            </button>
            <button onClick={onLogin} className="rounded-md border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50">
              I already have an account
            </button>
          </div>
        </section>

        <section className="border-y border-slate-200 bg-slate-50">
          <div className="mx-auto max-w-6xl px-5 py-14">
            <h2 className="text-xl font-bold">How it works</h2>
            <ol className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {steps.map((s) => (
                <li key={s.n} className="rounded-lg border border-slate-200 bg-white p-5">
                  <span className="text-sm font-bold text-cyan-700">Step {s.n}</span>
                  <h3 className="mt-1 font-semibold">{s.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{s.text}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-5 py-14">
          <h2 className="text-xl font-bold">Capabilities</h2>
          <div className="mt-6 grid gap-6 sm:grid-cols-2">
            {capabilities.map((c) => (
              <div key={c.title} className="border-l-2 border-cyan-700 pl-4">
                <h3 className="font-semibold">{c.title}</h3>
                <p className="mt-1 text-sm leading-6 text-slate-600">{c.text}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-5 pb-16">
          <div className="flex gap-3 rounded-lg border border-amber-200 bg-amber-50 p-5 text-sm leading-6 text-amber-900">
            <ShieldAlert size={20} className="mt-0.5 shrink-0" />
            <p>
              AI predictions are informational and are not a substitute for
              professional medical assessment. DermAI is an academic research
              prototype and is not clinically validated.
            </p>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        DermAI research prototype. Not for clinical use.
      </footer>
    </div>
  );
}
