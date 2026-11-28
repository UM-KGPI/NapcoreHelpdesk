/**
 * Layout wrapper for Q&A Assistant pages.
 * Includes the role switcher that allows navigation to Editorial Console.
 *
 * Created: 2026-07-02
 */

import React from "react";
import UserRoleSwitcher from "./UserRoleSwitcher";

interface UserPageLayoutProps {
  children: React.ReactNode;
}

export default function UserPageLayout({ children }: UserPageLayoutProps) {
  return (
    <>
      <UserRoleSwitcher />
      {children}
    </>
  );
}
