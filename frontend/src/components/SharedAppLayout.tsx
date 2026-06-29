/**
 * Shell layout with top navigation and auth state display.
 *
 * Wraps all routes via React Router's Outlet pattern. NavLink is used
 * instead of plain Link to enable automatic active-class highlighting.
 *
 * Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
 * Crafted by: AI coding agents
 * Created: 2026-03-29  |  Modified: 2026-06-28
 */

import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../auth-context";

interface SharedAppLayoutProps {
  appVersion: string;
  backendBuildRef: string;
}

function formatAppVersion(appVersion: string): string {
  const [baseVersion, buildMetadata] = appVersion.split("+", 2);
  if (!buildMetadata) {
    return appVersion;
  }
  return `${baseVersion} (${buildMetadata})`;
}

export default function SharedAppLayout({ appVersion, backendBuildRef }: SharedAppLayoutProps) {
  useAuth();

  return (
    <div className="page-shell">
      <header className="app-title-header">
        <h1>NAPCORE Helpdesk</h1>
        <p className="app-subtitle">Source-Grounded Q&A Assistant with Editorial knowledge building for Transmodel ecosystem</p>
        <p className="app-version-line">
          Frontend {formatAppVersion(appVersion)}
          {backendBuildRef && ` · Backend ${backendBuildRef}`}
        </p>
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
            Editorial Console
          </NavLink>
        </nav>
      </section>

      <Outlet />
    </div>
  );
}
