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

import { Outlet, NavLink, Link } from "react-router-dom";

import { useAuth } from "../auth-context";

interface SharedAppLayoutProps {
  appVersion: string;
  backendBuildRef: string;
}

function extractBaseVersion(appVersion: string): string {
  const [baseVersion] = appVersion.split("+", 2);
  return baseVersion;
}

export default function SharedAppLayout({ appVersion }: SharedAppLayoutProps) {
  useAuth();

  return (
    <div className="page-shell">
      <header className="app-title-header">
        <h1><Link to="/" className="app-title-link">NAPCORE Helpdesk</Link></h1>
        <p className="app-subtitle">Knowledge-Grounded, Multilingual AI Helpdesk for Mobility Data Standards (Transmodel Ecosystem) and EU Legislation (MMTIS, ITS Directive, TEL TSI)</p>
        <p className="app-version-line">
          v{extractBaseVersion(appVersion)} · {" "}
          <NavLink to="/about" className="app-about-link">
            About this project
          </NavLink>
        </p>
      </header>
      <Outlet />
    </div>
  );
}
