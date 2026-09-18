"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { Notice } from "@/components/notice";
import { errorMessage } from "@/lib/errors";
import { api } from "@/lib/services";

export default function RegisterPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSubmitting(true); setError("");
    const form = new FormData(event.currentTarget);
    try {
      await api.register(String(form.get("email")), String(form.get("password")));
      router.push("/login");
    } catch (reason) { setError(errorMessage(reason)); } finally { setSubmitting(false); }
  }

  return <main className="auth-page"><form className="card form-card" onSubmit={submit}><p className="eyebrow">Start here</p><h1>Create account</h1>{error && <Notice tone="error">{error}</Notice>}<label>Email<input name="email" type="email" required autoComplete="email" /></label><label>Password<input name="password" type="password" minLength={12} maxLength={128} required autoComplete="new-password" /><small>12–128 characters</small></label><button className="button button-primary" disabled={submitting}>{submitting ? "Creating…" : "Register"}</button><p className="muted">Already registered? <Link href="/login">Sign in</Link></p></form></main>;
}
