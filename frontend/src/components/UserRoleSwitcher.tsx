/**
 * Role switcher for Q&A Assistant section.
 * Shows button to navigate to Editorial Console only.
 *
 * Crafted by: AI coding agents
 * Created: 2026-07-02
 */

import { NavLink } from "react-router-dom";

export default function UserRoleSwitcher() {
  return (
    <section className="panel route-switcher-panel">
      <div className="route-switcher-copy">
        <h2>Role Switcher</h2>
      </div>
      <nav className="route-switcher-nav" aria-label="Workspace navigation">
        <NavLink to="/editor" className={({ isActive }) => `route-link ${isActive ? "route-link-active" : ""}`}>
          Editorial Console
        </NavLink>
      </nav>
    </section>
  );
}
