import { apiRequest } from "@/lib/api";
import type { AccessTokenResponse, Page, Ticket, TicketComment, TicketPriority, TicketStatus, User, UserRole } from "@/lib/types";

const API_PREFIX = "/api/v1";

export const api = {
  health: () => apiRequest<{ status: string }>("/health"),
  register: (email: string, password: string) => apiRequest<User>(`${API_PREFIX}/users/register`, { method: "POST", body: JSON.stringify({ email, password }) }),
  login: (email: string, password: string) => apiRequest<AccessTokenResponse>(`${API_PREFIX}/auth/login`, { method: "POST", body: JSON.stringify({ email, password }) }),
  me: (token: string) => apiRequest<User>(`${API_PREFIX}/users/me`, {}, token),
  tickets: (token: string, query: { page: number; status?: string; priority?: string }) => {
    const params = new URLSearchParams({ page: String(query.page) });
    if (query.status) params.set("status", query.status);
    if (query.priority) params.set("priority", query.priority);
    return apiRequest<Page<Ticket>>(`${API_PREFIX}/tickets?${params}`, {}, token);
  },
  ticket: (token: string, id: string) => apiRequest<Ticket>(`${API_PREFIX}/tickets/${id}`, {}, token),
  createTicket: (token: string, data: { title: string; description: string; priority: TicketPriority }) => apiRequest<Ticket>(`${API_PREFIX}/tickets`, { method: "POST", body: JSON.stringify(data) }, token),
  assignTicket: (token: string, id: string) => apiRequest<Ticket>(`${API_PREFIX}/tickets/${id}/assign`, { method: "POST" }, token),
  changeStatus: (token: string, id: string, status: TicketStatus) => apiRequest<Ticket>(`${API_PREFIX}/tickets/${id}/status`, { method: "PATCH", body: JSON.stringify({ status }) }, token),
  changePriority: (token: string, id: string, priority: TicketPriority) => apiRequest<Ticket>(`${API_PREFIX}/tickets/${id}/priority`, { method: "PATCH", body: JSON.stringify({ priority }) }, token),
  comments: (token: string, ticketId: string) => apiRequest<Page<TicketComment>>(`${API_PREFIX}/tickets/${ticketId}/comments?page_size=100`, {}, token),
  addComment: (token: string, ticketId: string, content: string) => apiRequest<TicketComment>(`${API_PREFIX}/tickets/${ticketId}/comments`, { method: "POST", body: JSON.stringify({ content }) }, token),
  users: (token: string, page = 1) => apiRequest<Page<User>>(`${API_PREFIX}/admin/users?page=${page}&page_size=100`, {}, token),
  changeUserRole: (token: string, id: string, role: UserRole) => apiRequest<User>(`${API_PREFIX}/admin/users/${id}/role`, { method: "PATCH", body: JSON.stringify({ role }) }, token),
  changeBlocked: (token: string, id: string, isBlocked: boolean) => apiRequest<User>(`${API_PREFIX}/admin/users/${id}/blocked`, { method: "PATCH", body: JSON.stringify({ is_blocked: isBlocked }) }, token),
  reassign: (token: string, ticketId: string, assigneeId: string) => apiRequest<Ticket>(`${API_PREFIX}/admin/tickets/${ticketId}/assignee`, { method: "PATCH", body: JSON.stringify({ assignee_id: assigneeId }) }, token),
};
