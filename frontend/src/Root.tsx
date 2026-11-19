import { useEffect, useState } from "react";
import App from "./App";
import Landing from "./components/Landing";
import Login from "./components/Login";
import Register from "./components/Register";
import { refreshAccessToken } from "./api/client";

type Screen = "loading" | "landing" | "login" | "register" | "app";

export default function Root() {
  const [screen, setScreen] = useState<Screen>("loading");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    refreshAccessToken().then((ok) => setScreen(ok ? "app" : "landing"));
  }, []);

  if (screen === "loading") {
    return <div className="p-8 text-sm text-slate-500">Loading...</div>;
  }
  if (screen === "app") return <App />;
  if (screen === "register") {
    return (
      <Register
        onRegistered={() => { setNotice("Account created. Please log in."); setScreen("login"); }}
        onLogin={() => setScreen("login")}
        onBack={() => setScreen("landing")}
      />
    );
  }
  if (screen === "login") {
    return (
      <div>
        <div className="flex justify-between bg-slate-50 px-5 pt-4 text-sm">
          <button onClick={() => setScreen("landing")} className="text-slate-500 hover:underline">Back to home</button>
          <button onClick={() => setScreen("register")} className="text-cyan-700 hover:underline">Create account</button>
        </div>
        {notice && <p className="bg-green-50 px-5 py-2 text-sm text-green-800">{notice}</p>}
        <Login onLoginSuccess={() => setScreen("app")} />
      </div>
    );
  }
  return <Landing onLogin={() => setScreen("login")} onRegister={() => setScreen("register")} />;
}
