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