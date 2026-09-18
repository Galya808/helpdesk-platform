"use client";

import Link from "next/link";

import { useAuth } from "@/components/auth-provider";

export function Protected({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <main className="page"><p>Loading session…</p></main>;
  if (!user) return <main className="page"><div className="card"><h1>Sign in required</h1><p className="muted">You need an account to use the helpdesk workspace.</p><Link className="button button-primary mt-4" href="/login">Sign in</Link></div></main>;
  return children;
}
