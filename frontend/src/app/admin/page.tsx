"use client";

import { useCallback, useEffect, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { Notice } from "@/components/notice";
import { Protected } from "@/components/protected";
import { errorMessage } from "@/lib/errors";
import { api } from "@/lib/services";
import type { User, UserRole } from "@/lib/types";

export default function AdminPage() {
  const { token, user } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!token || user?.role !== "admin") return;
    try { setUsers((await api.users(token)).items); }
    catch (reason) { setError(errorMessage(reason)); }
    finally { setLoading(false); }
  }, [token, user?.role]);

  useEffect(() => {
    const timeout = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timeout);
  }, [load]);

  async function update(operation: () => Promise<unknown>) {
    try { setError(""); await operation(); await load(); }
    catch (reason) { setError(errorMessage(reason)); }
  }

  return <Protected><main className="page"><div className="page-heading"><div><p className="eyebrow">Administration</p><h1>Users</h1></div><span className="pill">{users.length} users</span></div>{error && <Notice tone="error">{error}</Notice>}{user?.role !== "admin" ? <Notice tone="error">Administrator access required.</Notice> : loading ? <p>Loading users…</p> : <div className="card table-wrap"><table><thead><tr><th>User</th><th>Role</th><th>Status</th><th>Created</th></tr></thead><tbody>{users.map((item) => <tr key={item.id}><td><strong>{item.email}</strong><small>{item.id}</small></td><td><select value={item.role} disabled={item.id === user.id} onChange={(event) => token && update(() => api.changeUserRole(token, item.id, event.target.value as UserRole))}><option value="customer">Customer</option><option value="support_agent">Support agent</option><option value="admin">Admin</option></select></td><td><button className={`button ${item.is_blocked ? "button-primary" : "button-secondary"}`} disabled={item.id === user.id} onClick={() => token && update(() => api.changeBlocked(token, item.id, !item.is_blocked))}>{item.is_blocked ? "Unblock" : "Block"}</button></td><td>{new Date(item.created_at).toLocaleDateString()}</td></tr>)}</tbody></table></div>}</main></Protected>;
}
