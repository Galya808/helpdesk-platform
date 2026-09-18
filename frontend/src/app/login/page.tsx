"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { Notice } from "@/components/notice";
import { errorMessage } from "@/lib/errors";
import { api } from "@/lib/services";

export default function LoginPage() {
  const { setSession } = useAuth();
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true); setError("");
    const form = new FormData(event.currentTarget);
    try {
      const result = await api.login(String(form.get("email")), String(form.get("password")));
      await setSession(result.access_token);
      router.push("/tickets");
    } catch (reason) { setError(errorMessage(reason)); } finally { setSubmitting(false); }
  }

  return <main className="auth-page"><form className="card form-card" onSubmit={submit}><p className="eyebrow">Welcome back</p><h1>Sign in</h1>{error && <Notice tone="error">{error}</Notice>}<label>Email<input name="email" type="email" required autoComplete="email" /></label><label>Password<input name="password" type="password" minLength={12} required autoComplete="current-password" /></label><button className="button button-primary" disabled={submitting}>{submitting ? "Signing in…" : "Sign in"}</button><p className="muted">No account? <Link href="/register">Register</Link></p></form></main>;
}
