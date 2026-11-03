/**
 * Who is using the editor: sign-in with GitHub, the account bar, and the gate in front of the
 * editorial tabs.
 *
 * Without GitHub sign-in configured on the server the editor works as before (the auto-issued
 * token). With it, the anonymous token can only ask questions, so the editor asks people to sign in.
 *
 * Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
 * Crafted by: AI coding agents
 * Created: 2026-11-03  |  Modified: 2026-11-03
 */

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import type { HelpdeskApiClient } from "../api";
import type { AuthMe } from "../types";

interface EditorAccessValue {
  me: AuthMe | null;
  isAdmin: boolean;
  client: HelpdeskApiClient;
}

const EditorAccessContext = createContext<EditorAccessValue | null>(null);

export function useEditorAccess(): EditorAccessValue | null {
  return useContext(EditorAccessContext);
}

interface EditorAccessProps {
  client: HelpdeskApiClient;
  token: string;
  // The GitHub sign-in ended with an error (from the callback), shown once.
  signInError: string;
  onSignOut: () => void;
  children: ReactNode;
}

export default function EditorAccess({ client, token, signInError, onSignOut, children }: EditorAccessProps) {
  const [me, setMe] = useState<AuthMe | null>(null);
  const [githubSignIn, setGithubSignIn] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    client
      .getAuthConfig()
      .then((config) => !cancelled && setGithubSignIn(config.githubSignIn))
      .catch(() => !cancelled && setGithubSignIn(false));
    return () => {
      cancelled = true;
    };
  }, [client]);

  useEffect(() => {
    let cancelled = false;
    if (!token) {
      setMe(null);
      return;
    }
    client
      .getMe()
      .then((value) => !cancelled && setMe(value))
      .catch(() => !cancelled && setMe(null));
    return () => {
      cancelled = true;
    };
  }, [client, token]);

  const value = useMemo(
    () => ({ me, isAdmin: Boolean(me?.roles.includes("admin")), client }),
    [me, client],
  );
  const signedIn = me?.kind === "account" && me.account !== null;

  return (
    <EditorAccessContext.Provider value={value}>
      {githubSignIn && (
        <div className="panel editor-account-bar">
          {signedIn && me?.account ? (
            <>
              {me.account.avatarUrl && <img className="editor-account-avatar" src={me.account.avatarUrl} alt="" />}
              <span>
                Signed in as <strong>{me.account.name || me.account.githubLogin}</strong>
                <span className="muted"> (@{me.account.githubLogin}: {me.roles.join(", ")})</span>
              </span>
              <button type="button" onClick={onSignOut}>Sign out</button>
            </>
          ) : (
            <span className="muted">Not signed in.</span>
          )}
        </div>
      )}
      {signInError && <p className="error-text">{signInError}</p>}
      {githubSignIn && !signedIn ? (
        <section className="panel editor-sign-in">
          <h2>Sign in to the editor</h2>
          <p className="muted">
            Editorial work (review, FAQ, harvesting and indexing) needs an editor account. Sign in with the GitHub
            account an admin invited.
          </p>
          <a className="button-link" href={client.githubSignInUrl()}>Sign in with GitHub</a>
        </section>
      ) : (
        githubSignIn !== null && children
      )}
    </EditorAccessContext.Provider>
  );
}
