import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../auth-context";

interface SharedAppLayoutProps {
  frontendVersion: string;
  backendVersion: string;
  backendBuildRef: string;
}

export default function SharedAppLayout({ frontendVersion, backendVersion, backendBuildRef }: SharedAppLayoutProps) {
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
      <header className="app-title-header">
        <h1>NAPCORE Helpdesk</h1>
        <p className="app-subtitle">Source-Grounded Q&A Assistant with Editorial knowledge building for Transmodel ecosystem</p>
        <p className="app-version-line">Frontend v{frontendVersion} · Backend v{backendVersion} ({backendBuildRef})</p>
      </header>
      <section className="panel route-switcher-panel">
        <div className="route-switcher-copy">
          <h2>Role Switcher</h2>
        </div>
        <nav className="route-switcher-nav" aria-label="Workspace navigation">
          <NavLink to="/user" className={({ isActive }) => `route-link ${isActive ? "route-link-active" : ""}`}>
            Q&amp;A Asisstant
          </NavLink>
          <NavLink to="/editor" className={({ isActive }) => `route-link ${isActive ? "route-link-active" : ""}`}>
            Editor Console
          </NavLink>
        </nav>
      </section>

      <Outlet />

      <details className="panel credentials-panel system-panel collapsible-panel">
        <summary className="collapsible-summary">
          <div className="system-panel-header">
            <p className="kicker">System Settings</p>
            <h2>Connection</h2>
            <p className="muted">API and token settings live here when you need to troubleshoot or switch environments.</p>
          </div>
        </summary>
        <div className="collapsible-body">
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
        </div>
      </details>
    </div>
  );
}
