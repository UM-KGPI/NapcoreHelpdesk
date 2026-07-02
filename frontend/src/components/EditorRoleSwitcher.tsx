/**
 * Role switcher for Editorial Console section.
 * Shows button to navigate to Q&A Assistant only.
 *
 * Crafted by: AI coding agents
 * Created: 2026-07-02
 */

import { NavLink } from "react-router-dom";

export default function EditorRoleSwitcher() {
  return (
    <section className="panel route-switcher-panel">
      <div className="route-switcher-copy">
        <h2>Role Switcher</h2>
      </div>
      <nav className="route-switcher-nav" aria-label="Workspace navigation">
        <NavLink to="/user" className={({ isActive }) => `route-link ${isActive ? "route-link-active" : ""}`}>
          Q&amp;A Assistant
        </NavLink>
      </nav>
    </section>
  );
}
