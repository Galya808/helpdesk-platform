"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { useAuth } from "@/components/auth-provider";
import { Notice } from "@/components/notice";
import { Protected } from "@/components/protected";
import { errorMessage } from "@/lib/errors";
import { api } from "@/lib/services";
import type { Ticket, TicketComment, TicketPriority, TicketStatus, User } from "@/lib/types";

export default function TicketDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { token, user } = useAuth();
  const role = user?.role;
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [comments, setComments] = useState<TicketComment[]>([]);
  const [agents, setAgents] = useState<User[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!token) return;
    try {
      const [ticketResult, commentResult] = await Promise.all([api.ticket(token, id), api.comments(token, id)]);
      setTicket(ticketResult); setComments(commentResult.items);
      if (role === "admin") {
        const users = await api.users(token);
        setAgents(users.items.filter((item) => item.role === "support_agent" && !item.is_blocked));
      }
    } catch (reason) { setError(errorMessage(reason)); }
    finally { setLoading(false); }
  }, [token, id, role]);

  useEffect(() => {
    const timeout = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timeout);
  }, [load]);

  async function action(operation: () => Promise<unknown>) {
    try { setError(""); await operation(); await load(); }
    catch (reason) { setError(errorMessage(reason)); }
  }

  async function addComment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!token) return;
    const form = event.currentTarget;
    const content = String(new FormData(form).get("content"));
    await action(() => api.addComment(token, id, content));
    form.reset();
  }

  return <Protected><main className="page">{error && <Notice tone="error">{error}</Notice>}{loading && <p>Loading ticket…</p>}{ticket && <>
    <div className="page-heading"><div><p className="eyebrow">Ticket detail</p><h1>{ticket.title}</h1></div><span className={`badge priority-${ticket.priority}`}>{ticket.priority}</span></div>
    <section className="card stack"><div className="ticket-meta"><span className="badge">{ticket.status.replace("_", " ")}</span><span className="muted">Created {new Date(ticket.created_at).toLocaleString()}</span></div><p className="description">{ticket.description}</p><dl className="detail-grid"><div><dt>Customer</dt><dd>{ticket.customer_id}</dd></div><div><dt>Assignee</dt><dd>{ticket.assignee_id ?? "Unassigned"}</dd></div></dl></section>
    <section className="card"><h2>Actions</h2><div className="action-grid">
      {user?.role === "support_agent" && !ticket.assignee_id && <button className="button button-primary" onClick={() => token && action(() => api.assignTicket(token, id))}>Assign to me</button>}
      <label>Status<select value={ticket.status} onChange={(event) => token && action(() => api.changeStatus(token, id, event.target.value as TicketStatus))}><option value="open">Open</option><option value="in_progress">In progress</option><option value="resolved">Resolved</option><option value="closed">Closed</option></select></label>
      {(user?.role === "support_agent" || user?.role === "admin") && <label>Priority<select value={ticket.priority} onChange={(event) => token && action(() => api.changePriority(token, id, event.target.value as TicketPriority))}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="urgent">Urgent</option></select></label>}
      {user?.role === "admin" && <label>Assignee<select value={ticket.assignee_id ?? ""} onChange={(event) => token && event.target.value && action(() => api.reassign(token, id, event.target.value))}><option value="">Choose active agent</option>{agents.map((agent) => <option key={agent.id} value={agent.id}>{agent.email}</option>)}</select></label>}
    </div></section>
    <section className="card stack"><h2>Comments</h2>{comments.length ? comments.map((comment) => <article className="comment" key={comment.id}><div className="comment-head"><strong>{comment.author_id === user?.id ? "You" : comment.author_id}</strong><span>{new Date(comment.created_at).toLocaleString()}</span></div><p>{comment.content}</p></article>) : <p className="empty">No comments yet.</p>}{ticket.status !== "closed" && <form className="comment-form" onSubmit={addComment}><label>Add comment<textarea name="content" rows={3} maxLength={5000} required /></label><button className="button button-primary">Post comment</button></form>}</section>
  </>}</main></Protected>;
}
