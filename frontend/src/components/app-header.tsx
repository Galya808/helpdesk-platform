"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth-provider";

export function AppHeader() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex min-h-16 max-w-6xl items-center justify-between gap-4 px-4">
        <Link href="/" className="text-lg font-bold text-slate-900">Helpdesk</Link>
        <nav className="flex items-center gap-3 text-sm">
          {user && <Link href="/tickets">Tickets</Link>}
          {user?.role === "admin" && <Link href="/admin">Users</Link>}
          {!loading && !user && <Link href="/login">Sign in</Link>}
          {!loading && !user && <Link className="button button-primary" href="/register">Register</Link>}
          {user && (
            <>
              <span className="hidden text-slate-500 sm:inline">{user.email}</span>
              <button className="button button-secondary" onClick={() => { logout(); router.push("/"); }}>Sign out</button>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
