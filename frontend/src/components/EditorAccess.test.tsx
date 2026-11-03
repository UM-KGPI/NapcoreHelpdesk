import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { HelpdeskApiClient } from "../api";
import type { AuthMe, EditorUser } from "../types";
import EditorAccess, { useEditorAccess } from "./EditorAccess";
import UsersPanel from "./UsersPanel";

const ALICE: EditorUser = {
  id: 1,
  githubLogin: "alice",
  name: "Alice A.",
  avatarUrl: "",
  roles: ["admin"],
  isActive: true,
  signedInOnce: true,
  invitedBy: "EDITOR_ADMIN_GITHUB_LOGINS",
  lastLoginAt: null,
  createdAt: "2026-11-03T00:00:00Z",
};

function client(githubSignIn: boolean, me: AuthMe): HelpdeskApiClient {
  return {
    getAuthConfig: vi.fn().mockResolvedValue({ githubSignIn }),
    getMe: vi.fn().mockResolvedValue(me),
    githubSignInUrl: () => "http://api.test/api/v1/auth/github/login",
  } as unknown as HelpdeskApiClient;
}

const ANONYMOUS: AuthMe = { subject: "user-local", kind: "anonymous", roles: ["reader"], account: null, githubSignIn: true };
const SIGNED_IN: AuthMe = { subject: "github:1", kind: "account", roles: ["admin"], account: ALICE, githubSignIn: true };

function AdminFlag() {
  return <p>{useEditorAccess()?.isAdmin ? "admin view" : "editor view"}</p>;
}

describe("EditorAccess", () => {
  afterEach(cleanup);

  it("keeps the editor open when GitHub sign-in is not configured", async () => {
    render(
      <EditorAccess client={client(false, ANONYMOUS)} token="t" signInError="" onSignOut={() => {}}>
        <AdminFlag />
      </EditorAccess>,
    );
    expect(await screen.findByText("editor view")).toBeTruthy();
    expect(screen.queryByText("Sign in with GitHub")).toBeNull();
  });

  it("asks an anonymous visitor to sign in instead of showing the editor", async () => {
    render(
      <EditorAccess client={client(true, ANONYMOUS)} token="t" signInError="GitHub user bob has no editor account." onSignOut={() => {}}>
        <AdminFlag />
      </EditorAccess>,
    );
    const link = await screen.findByRole("link", { name: "Sign in with GitHub" });
    expect(link.getAttribute("href")).toBe("http://api.test/api/v1/auth/github/login");
    expect(screen.getByText("GitHub user bob has no editor account.")).toBeTruthy();
    expect(screen.queryByText("editor view")).toBeNull();
  });

  it("shows the signed-in account and its admin rights", async () => {
    const onSignOut = vi.fn();
    render(
      <EditorAccess client={client(true, SIGNED_IN)} token="t" signInError="" onSignOut={onSignOut}>
        <AdminFlag />
      </EditorAccess>,
    );
    expect(await screen.findByText("admin view")).toBeTruthy();
    expect(screen.getByText("Alice A.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Sign out" }));
    expect(onSignOut).toHaveBeenCalled();
  });
});

describe("UsersPanel", () => {
  afterEach(cleanup);

  it("lists accounts, invites a login and changes roles", async () => {
    const api = {
      listUsers: vi.fn().mockResolvedValue({ users: [ALICE], roles: ["editor", "reviewer", "publisher", "admin"] }),
      inviteUser: vi.fn().mockResolvedValue({ user: { ...ALICE, id: 2, githubLogin: "carol" } }),
      updateUser: vi.fn().mockResolvedValue({ user: ALICE }),
    } as unknown as HelpdeskApiClient;
    render(<UsersPanel client={api} />);

    expect(await screen.findByRole("link", { name: "@alice" })).toBeTruthy();
    fireEvent.change(screen.getByLabelText("GitHub login"), { target: { value: "carol" } });
    fireEvent.click(screen.getByRole("button", { name: "Invite" }));
    await waitFor(() => expect(api.inviteUser).toHaveBeenCalledWith("carol", ["editor"]));

    fireEvent.click(screen.getByLabelText("reviewer for alice"));
    await waitFor(() => expect(api.updateUser).toHaveBeenCalledWith(1, { roles: ["admin", "reviewer"] }));
  });
});
