/**
 * Shell layout with top navigation and auth state display.
 *
 * Wraps all routes via React Router's Outlet pattern. NavLink is used
 * instead of plain Link to enable automatic active-class highlighting.
 *
 * Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
 * Crafted by: AI coding agents
 * Created: 2026-03-29  |  Modified: 2026-11-11
 */

import { Outlet, NavLink, Link } from "react-router-dom";

import { useAuth } from "../auth-context";
import ServiceStatusBanner from "./ServiceStatusBanner";
import coFundedByTheEuUrl from "../assets/brand/co-funded-by-the-eu-negative.png";
import napcoreLogoUrl from "../assets/brand/napcore-logo-white.svg";

interface SharedAppLayoutProps {
  appVersion: string;
  backendBuildRef: string;
  apiBaseUrl: string;
}

function extractBaseVersion(appVersion: string): string {
  const [baseVersion] = appVersion.split("+", 2);
  return baseVersion;
}

// NAPCORE branding (#377), Sara's glass design: the NAPCORE logo (white lettering) in the header, the EU
// emblem with its funding statement in the footer. Both sit on dark glass, so the emblem is the Commission's
// negative version (white statement, white border around the flag; guidelines 2021-2027, p. 5), unmodified,
// and its flag is as tall as the NAPCORE logo (pp. 4, 12).
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
      <header className="app-title-header glass">
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
      <footer className="app-footer glass">
        <CoFundedByTheEu />
      </footer>
    </div>
  );
}
