"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { api } from "@/lib/services";
import type { User } from "@/lib/types";

const TOKEN_KEY = "helpdesk_access_token";

type AuthContextValue = {
  token: string | null;
  user: User | null;
  loading: boolean;
  setSession: (token: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  async function setSession(nextToken: string) {
    const currentUser = await api.me(nextToken);
    localStorage.setItem(TOKEN_KEY, nextToken);
    setToken(nextToken);
    setUser(currentUser);
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }

  useEffect(() => {
    async function restoreSession() {
      await Promise.resolve();
      const storedToken = localStorage.getItem(TOKEN_KEY);
      if (!storedToken) {
        setLoading(false);
        return;
      }
      try {
        const currentUser = await api.me(storedToken);
        setToken(storedToken);
        setUser(currentUser);
      } catch {
        localStorage.removeItem(TOKEN_KEY);
      } finally {
        setLoading(false);
      }
    }
    void restoreSession();
  }, []);

  const value = useMemo(
    () => ({ token, user, loading, setSession, logout }),
    [token, user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
