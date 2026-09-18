"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { Notice } from "@/components/notice";
import { errorMessage } from "@/lib/errors";
import { api } from "@/lib/services";

export default function Home() {
  const { user } = useAuth();
  const [health, setHealth] = useState<"loading" | "online" | "offline">("loading");
  const [error, setError] = useState("");

  useEffect(() => {
    api.health()
      .then(() => setHealth("online"))
      .catch((reason) => { setHealth("offline"); setError(errorMessage(reason)); });
  }, []);

  return (
    <main className="page">
      <section className="hero">
        <div>
          <p className="eyebrow">Support without the clutter</p>
          <h1>One clear workspace for every support request.</h1>
          <p className="hero-copy">Create, assign, discuss, resolve, and audit tickets through a role-aware interface powered by the FastAPI backend.</p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link className="button button-primary" href={user ? "/tickets" : "/register"}>{user ? "Open workspace" : "Create account"}</Link>
            {!user && <Link className="button button-secondary" href="/login">Sign in</Link>}
          </div>
        </div>
        <div className="card status-card">
          <span className={`status-dot status-${health}`} />
          <div>
            <strong>Backend {health}</strong>
            <p className="muted">FastAPI health check</p>
          </div>
        </div>
      </section>
      {error && <Notice tone="error">{error}</Notice>}
      <section className="feature-grid">
        <article className="card"><h2>Customers</h2><p>Create tickets, follow progress, comment, and close resolved requests.</p></article>
        <article className="card"><h2>Support agents</h2><p>Take unassigned work, manage priority, communicate, and resolve issues.</p></article>
        <article className="card"><h2>Administrators</h2><p>Manage users, roles, blocked accounts, and ticket assignments.</p></article>
      </section>
    </main>
  );
}
