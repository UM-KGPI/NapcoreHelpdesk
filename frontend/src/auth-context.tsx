/**
 * React context for JWT token state and dev token issuance.
 *
 * Provides the token string and an auto-token flag to all components.
 * The dev-token endpoint is available only when the backend is running in
 * development mode; production traffic goes through the real identity provider.
 *
 * Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
 * Crafted by: AI coding agents
 * Created: 2026-03-29  |  Modified: 2026-06-28
 */

import type { ReactNode } from "react";
import { createContext, useContext } from "react";

interface AuthContextValue {
  apiBaseUrl: string;
  setApiBaseUrl: (value: string) => void;
  token: string;
  setToken: (value: string) => void;
  autoTokenEnabled: boolean;
  setAutoTokenEnabled: (value: boolean) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ value, children }: { value: AuthContextValue; children: ReactNode }) {
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
