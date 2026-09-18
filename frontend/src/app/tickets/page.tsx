"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { Notice } from "@/components/notice";
import { Protected } from "@/components/protected";
import { errorMessage } from "@/lib/errors";
import { api } from "@/lib/services";
import type { Page, Ticket, TicketPriority } from "@/lib/types";

export default function TicketsPage() {
  const { token, user } = useAuth();
  const [result, setResult] = useState<Page<Ticket> | null>(null);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!token) return;
    try { setResult(await api.tickets(token, { page, status: statusFilter, priority: priorityFilter })); }
    catch (reason) { setError(errorMessage(reason)); }
    finally { setLoading(false); }
  }, [token, page, statusFilter, priorityFilter]);

  useEffect(() => {
    const timeout = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timeout);
  }, [load]);

  async function createTicket(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    try {
      await api.createTicket(token, {
        title: String(data.get("title")),
        description: String(data.get("description")),
        priority: String(data.get("priority")) as TicketPriority,
      });
      form.reset(); setPage(1); await load();
    } catch (reason) { setError(errorMessage(reason)); }
  }

  return (
    <Protected><main className="page"><div className="page-heading"><div><p className="eyebrow">{user?.role.replace("_", " ")}</p><h1>Tickets</h1></div><span className="pill">{result?.total ?? 0} total</span></div>
      {error && <Notice tone="error">{error}</Notice>}
      {user?.role === "customer" && <form className="card form-grid" onSubmit={createTicket}><h2>Create a ticket</h2><label>Title<input name="title" minLength={3} maxLength={200} required /></label><label>Priority<select name="priority" defaultValue="medium"><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="urgent">Urgent</option></select></label><label className="full">Description<textarea name="description" minLength={10} maxLength={10000} rows={4} required /></label><button className="button button-primary">Create ticket</button></form>}
      <section className="card"><div className="filters"><label>Status<select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}><option value="">All</option><option value="open">Open</option><option value="in_progress">In progress</option><option value="resolved">Resolved</option><option value="closed">Closed</option></select></label><label>Priority<select value={priorityFilter} onChange={(e) => { setPriorityFilter(e.target.value); setPage(1); }}><option value="">All</option><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="urgent">Urgent</option></select></label></div>
        {loading ? <p>Loading tickets…</p> : result?.items.length ? <div className="ticket-list">{result.items.map((ticket) => <Link className="ticket-row" key={ticket.id} href={`/tickets/${ticket.id}`}><div><strong>{ticket.title}</strong><p className="muted">{new Date(ticket.created_at).toLocaleString()}</p></div><div className="ticket-meta"><span className={`badge priority-${ticket.priority}`}>{ticket.priority}</span><span className="badge">{ticket.status.replace("_", " ")}</span></div></Link>)}</div> : <p className="empty">No tickets match these filters.</p>}
        {result && result.pages > 1 && <div className="pagination"><button className="button button-secondary" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>Previous</button><span>Page {page} of {result.pages}</span><button className="button button-secondary" disabled={page >= result.pages} onClick={() => setPage((value) => value + 1)}>Next</button></div>}
      </section>
    </main></Protected>
  );
}
