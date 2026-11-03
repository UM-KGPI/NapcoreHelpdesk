/**
 * Editor > Users (admins): invite a GitHub login with roles, change roles, disable or remove an account.
 *
 * Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
 * Crafted by: AI coding agents
 * Created: 2026-11-03  |  Modified: 2026-11-03
 */

import { useCallback, useEffect, useState, type FormEvent } from "react";
import type { HelpdeskApiClient } from "../api";
import type { EditorRole, EditorUser } from "../types";

const ROLES: EditorRole[] = ["editor", "reviewer", "publisher", "admin"];

const ROLE_NOTES: Record<EditorRole, string> = {
  editor: "queues answers for review",
  reviewer: "approves, rejects and revokes",
  publisher: "publishes FAQs, harvests and indexes sources",
  admin: "everything, and manages users",
};

function errorText(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}

export default function UsersPanel({ client }: { client: HelpdeskApiClient }) {
  const [users, setUsers] = useState<EditorUser[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [login, setLogin] = useState("");
  const [inviteRoles, setInviteRoles] = useState<EditorRole[]>(["editor"]);

  const load = useCallback(async () => {
    try {
      setUsers((await client.listUsers()).users);
      setError(null);
    } catch (err) {
      setError(errorText(err));
    }
  }, [client]);

  useEffect(() => {
    void load();
  }, [load]);

  async function run(action: () => Promise<unknown>): Promise<void> {
    try {
      await action();
      await load();
    } catch (err) {
      setError(errorText(err));
    }
  }

  async function onInvite(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    await run(async () => {
      await client.inviteUser(login, inviteRoles);
      setLogin("");
    });
  }

  function toggle(roles: EditorRole[], role: EditorRole): EditorRole[] {
    return roles.includes(role) ? roles.filter((item) => item !== role) : [...roles, role];
  }

  return (
    <section className="panel">
      <div className="panel-title-row">
        <h2>Users</h2>
        <p className="muted">People sign in with GitHub. Invite a GitHub login with roles; the invitation is used at the first sign-in.</p>
      </div>
      {error && <p className="error-text">{error}</p>}

      <form className="stack" onSubmit={(event) => void onInvite(event)}>
        <label>
          GitHub login
          <input type="text" value={login} onChange={(e) => setLogin(e.target.value)} placeholder="octocat" required />
        </label>
        <fieldset className="role-options">
          <legend>Roles</legend>
          {ROLES.map((role) => (
            <label key={role} className="checkbox-label">
              <input
                type="checkbox"
                checked={inviteRoles.includes(role)}
                onChange={() => setInviteRoles((current) => toggle(current, role))}
              />
              {role} <span className="muted tiny">({ROLE_NOTES[role]})</span>
            </label>
          ))}
        </fieldset>
        <button type="submit" disabled={!login.trim() || inviteRoles.length === 0}>Invite</button>
      </form>

      <div className="table-wrap">
        <table className="board-table">
          <thead>
            <tr>
              <th>GitHub login</th>
              {ROLES.map((role) => <th key={role}>{role}</th>)}
              <th>Status</th>
              <th>Last sign-in</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id} className={user.isActive ? undefined : "muted"}>
                <td>
                  <a href={`https://github.com/${user.githubLogin}`} target="_blank" rel="noreferrer">@{user.githubLogin}</a>
                  {user.name && <span className="muted"> {user.name}</span>}
                </td>
                {ROLES.map((role) => (
                  <td key={role}>
                    <input
                      type="checkbox"
                      aria-label={`${role} for ${user.githubLogin}`}
                      checked={user.roles.includes(role)}
                      onChange={() => void run(() => client.updateUser(user.id, { roles: toggle(user.roles, role) }))}
                    />
                  </td>
                ))}
                <td>{!user.isActive ? "disabled" : user.signedInOnce ? "active" : "invited"}</td>
                <td>{user.lastLoginAt ? new Date(user.lastLoginAt).toLocaleString() : "—"}</td>
                <td className="button-row">
                  <button type="button" onClick={() => void run(() => client.updateUser(user.id, { isActive: !user.isActive }))}>
                    {user.isActive ? "Disable" : "Enable"}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      if (window.confirm(`Remove the editor account of @${user.githubLogin}?`)) {
                        void run(() => client.deleteUser(user.id));
                      }
                    }}
                  >
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
