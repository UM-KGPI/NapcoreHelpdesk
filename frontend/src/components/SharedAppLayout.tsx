import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../auth-context";

export default function SharedAppLayout() {
  const {
    apiBaseUrl,
    setApiBaseUrl,
    token,
    setToken,
    autoTokenEnabled,
    setAutoTokenEnabled,
  } = useAuth();

  return (
    <div className="page-shell">
      <header className="hero">
        <p className="kicker">NAPCORE HELPDESK</p>
        <h1>Q&amp;A about NAPCORE related multimodal standardisation</h1>
        <p className="subhead">Demonstration shell with separate user and operator surfaces sharing one backend connection.</p>
      </header>

      <section className="panel route-switcher-panel">
        <div className="route-switcher-copy">
          <h2>Experience Switcher</h2>
          <p className="muted">Use separate routes for demo: user-facing chat and operator-facing console are now independently addressable.</p>
        </div>
        <nav className="route-switcher-nav" aria-label="Workspace navigation">
          <NavLink to="/user" className={({ isActive }) => `route-link ${isActive ? "route-link-active" : ""}`}>
            User Chat
          </NavLink>
          <NavLink to="/operator" className={({ isActive }) => `route-link ${isActive ? "route-link-active" : ""}`}>
            Operator Console
          </NavLink>
        </nav>
      </section>

      <section className="panel credentials-panel">
        <h2>Connection</h2>
        <div className="grid-two">
          <label>
            API Base URL
            <input value={apiBaseUrl} onChange={(event) => setApiBaseUrl(event.target.value)} placeholder="/api/v1" />
          </label>
          <label>
            JWT Bearer Token
            <input value={token} onChange={(event) => setToken(event.target.value)} placeholder="Paste token" />
          </label>
        </div>
        <label className="checkbox-label">
          <input type="checkbox" checked={autoTokenEnabled} onChange={(event) => setAutoTokenEnabled(event.target.checked)} />
          auto-create dev JWT on page reload
        </label>
      </section>

      <Outlet />
    </div>
  );
}