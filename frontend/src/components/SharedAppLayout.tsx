/**
 * Shell layout with top navigation and auth state display.
 *
 * Wraps all routes via React Router's Outlet pattern. NavLink is used
 * instead of plain Link to enable automatic active-class highlighting.
 *
 * Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
 * Crafted by: AI coding agents
 * Created: 2026-03-29  |  Modified: 2026-11-10
 */

import { Outlet, NavLink, Link } from "react-router-dom";

import { useAuth } from "../auth-context";
import ServiceStatusBanner from "./ServiceStatusBanner";
import coFundedByTheEuUrl from "../assets/brand/co-funded-by-the-eu.png";
import napcoreLogoUrl from "../assets/brand/napcore-logo.svg";

interface SharedAppLayoutProps {
  appVersion: string;
  backendBuildRef: string;
  apiBaseUrl: string;
}

function extractBaseVersion(appVersion: string): string {
  const [baseVersion] = appVersion.split("+", 2);
  return baseVersion;
}

// NAPCORE branding (#377): the NAPCORE logo and the EU emblem with its funding statement, as published on
// napcore.eu, in the header and the footer. The emblem is shown unmodified, apart from the NAPCORE logo and
// at least as large as it (EU emblem guidelines 2021-2027, pp. 4, 9, 12).
function CoFundedByTheEu() {
  return (
    <img
      className="brand-eu-emblem"
      src={coFundedByTheEuUrl}
      alt="Co-funded by the European Union"
      width={4119}
      height={919}
    />
  );
}

export default function SharedAppLayout({ appVersion, apiBaseUrl }: SharedAppLayoutProps) {
  useAuth();

  return (
    <div className="page-shell">
      <header className="app-title-header">
        <img className="brand-napcore-logo" src={napcoreLogoUrl} alt="NAPCORE" width={3881} height={2665} />
        <div className="app-title-text">
          <h1><Link to="/" className="app-title-link">NAPCORE Helpdesk</Link></h1>
          <p className="app-subtitle">Knowledge-Grounded, Multilingual AI Helpdesk for Mobility Data Standards</p>
          <p className="app-version-line">
            v{extractBaseVersion(appVersion)} · {" "}
            <NavLink to="/about" className="app-about-link">
              About this project
            </NavLink>
          </p>
        </div>
      </header>
      <ServiceStatusBanner apiBaseUrl={apiBaseUrl} />
      <Outlet />
      <footer className="app-footer">
        <a href="https://napcore.eu/" target="_blank" rel="noreferrer" className="app-footer-napcore">
          <img className="brand-napcore-logo" src={napcoreLogoUrl} alt="NAPCORE" width={3881} height={2665} />
        </a>
        <nav className="app-footer-links" aria-label="Footer">
          <NavLink to="/about">About this project</NavLink>
          <a href="https://github.com/UM-KGPI/NapcoreHelpdesk" target="_blank" rel="noreferrer">Source code</a>
          <a href="https://www.gnu.org/licenses/agpl-3.0.html" target="_blank" rel="noreferrer">Licence (AGPL-3.0)</a>
        </nav>
        <CoFundedByTheEu />
      </footer>
    </div>
  );
}
