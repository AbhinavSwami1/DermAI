interface LandingProps {
  onLogin: () => void;
  onRegister: () => void;
}

const steps = [
  ["01", "Upload", "Choose a JPEG or PNG photograph of a skin area."],
  ["02", "Image check", "Blur, brightness and exposure are measured. Unsuitable images are flagged or blocked."],
  ["03", "Analysis", "A trained classifier scores six lesion categories."],
  ["04", "Review", "Read the Top-3 predictions and the Grad-CAM view, then export a report."],
];

const outputs = [
  ["Predicted condition", "The category with the highest model score."],
  ["Model score", "A softmax output. It is not a clinically validated probability."],
  ["Top three", "The three highest-scoring categories, so close calls are visible."],
  ["Grad-CAM view", "Image regions that influenced the score. It is not a lesion outline."],
  ["Record", "Model version and time, saved to your history and exportable as PDF, CSV or JSON."],
];

const notIncluded = [
  "Diagnosis or treatment advice",
  "Severity or risk rating (the dataset has no severity labels)",
  "Lesion segmentation or outlining",
  "Clinical validation",
];

export default function Landing({ onLogin, onRegister }: LandingProps) {
  return (
    <div className="min-h-screen bg-stone-100 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4 sm:px-8">
          <span className="font-serif text-xl font-semibold">DermAI</span>
          <nav className="flex items-center gap-2 text-sm" aria-label="Account">
            <button onClick={onLogin} className="px-3 py-2 text-slate-700 hover:text-slate-900">
              Log in
            </button>
            <button onClick={onRegister} className="rounded border border-slate-300 px-4 py-2 font-medium text-slate-800 hover:bg-slate-50">
              Register
            </button>
          </nav>
        </div>
      </header>

      <main>
        <section className="mx-auto grid max-w-6xl gap-12 px-5 py-14 sm:px-8 lg:grid-cols-5 lg:py-24">
          <div className="lg:col-span-3">
            <p className="text-sm text-slate-500">Skin image analysis for research</p>
            <h1 className="mt-4 text-4xl font-semibold leading-tight sm:text-5xl">
              See what a classifier predicts for a skin photograph, and how sure it is.
            </h1>
            <p className="mt-6 max-w-xl text-base leading-7 text-slate-600">
              DermAI checks the quality of an uploaded image, runs a trained deep-learning
              model, and reports the predicted condition together with the model&apos;s scores
              and the image regions behind them. It is built for screening research and
              decision support, not for diagnosis.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <button onClick={onRegister} className="rounded bg-cyan-700 px-5 py-3 text-sm font-medium text-white hover:bg-cyan-800">
                Start an analysis
              </button>
              <button onClick={onLogin} className="rounded border border-slate-300 bg-white px-5 py-3 text-sm font-medium text-slate-800 hover:bg-slate-50">
                Log in
              </button>
            </div>
          </div>

          <aside className="lg:col-span-2">
            <h2 className="text-lg font-semibold">What a result contains</h2>
            <dl className="mt-4 divide-y divide-slate-200 border-y border-slate-200">
              {outputs.map(([term, text]) => (
                <div key={term} className="py-3">
                  <dt className="text-sm font-medium text-slate-900">{term}</dt>
                  <dd className="mt-0.5 text-sm leading-6 text-slate-600">{text}</dd>
                </div>
              ))}
            </dl>
          </aside>
        </section>

        <section className="border-y border-slate-200 bg-white">
          <div className="mx-auto max-w-6xl px-5 py-14 sm:px-8">
            <h2 className="text-2xl font-semibold">How it works</h2>
            <ol className="mt-8 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
              {steps.map(([n, title, text]) => (
                <li key={n} className="border-t-2 border-cyan-700 pt-4">
                  <span className="font-serif text-sm text-slate-500">{n}</span>
                  <h3 className="mt-1 text-lg font-semibold">{title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{text}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section className="mx-auto grid max-w-6xl gap-10 px-5 py-14 sm:px-8 md:grid-cols-2">
          <div>
            <h2 className="text-2xl font-semibold">What it covers</h2>
            <p className="mt-4 text-sm leading-7 text-slate-600">
              Six categories from the PAD-UFES-20 dataset: actinic keratosis, basal cell
              carcinoma, melanoma, nevus, squamous cell carcinoma and seborrheic keratosis.
              Results are experimental and were measured on a small held-out test set.
            </p>
          </div>
          <div>
            <h2 className="text-2xl font-semibold">What it does not do</h2>
            <ul className="mt-4 space-y-2 text-sm leading-6 text-slate-600">
              {notIncluded.map((item) => (
                <li key={item} className="border-l-2 border-slate-300 pl-3">{item}</li>
              ))}
            </ul>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-5 pb-16 sm:px-8">
          <p className="border-l-4 border-amber-500 bg-white py-4 pl-5 pr-4 text-sm leading-6 text-slate-800">
            AI predictions are informational and are not a substitute for professional
            medical assessment. See a qualified clinician about any skin concern.
          </p>
        </section>
      </main>

      <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500">
        DermAI is an academic research prototype built on the PAD-UFES-20 dataset.
      </footer>
    </div>
  );
}
