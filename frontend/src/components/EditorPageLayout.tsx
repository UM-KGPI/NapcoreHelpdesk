/**
 * Layout wrapper for Editorial Console pages.
 * Includes the role switcher that allows navigation to Q&A Assistant.
 *
 * Created: 2026-07-02
 */

import React from "react";
import EditorRoleSwitcher from "./EditorRoleSwitcher";

interface EditorPageLayoutProps {
  children: React.ReactNode;
}

export default function EditorPageLayout({ children }: EditorPageLayoutProps) {
  return (
    <>
      <EditorRoleSwitcher />
      {children}
    </>
  );
}
