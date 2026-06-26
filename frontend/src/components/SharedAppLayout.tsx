import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../auth-context";

interface SharedAppLayoutProps {
  appVersion: string;
}

function formatAppVersion(appVersion: string): string {
  const [baseVersion, buildMetadata] = appVersion.split("+", 2);
  if (!buildMetadata) {
    return appVersion;
  }
  return `${baseVersion} (${buildMetadata})`;
}

export default function SharedAppLayout({ appVersion }: SharedAppLayoutProps) {
  useAuth();

  return (
    <div className="page-shell">
      <header className="app-title-header">
        <h1>NAPCORE Helpdesk</h1>
        <p className="app-subtitle">Source-Grounded Q&A Assistant with Editorial knowledge building for Transmodel ecosystem</p>
        <p className="app-version-line">Version {formatAppVersion(appVersion)}</p>
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
    </div>
  );
}
