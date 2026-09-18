export type UserRole = "customer" | "support_agent" | "admin";
export type TicketStatus = "open" | "in_progress" | "resolved" | "closed";
export type TicketPriority = "low" | "medium" | "high" | "urgent";

export type User = {
  id: string;
  email: string;
  role: UserRole;
  is_blocked: boolean;
  created_at: string;
  updated_at: string;
};

export type Ticket = {
  id: string;
  title: string;
  description: string;
  status: TicketStatus;
  priority: TicketPriority;
  customer_id: string;
  assignee_id: string | null;
  created_at: string;
  updated_at: string;
};

export type TicketComment = {
  id: string;
  ticket_id: string;
  author_id: string;
  content: string;
  created_at: string;
};

export type Page<T> = {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
};

export type AccessTokenResponse = {
  access_token: string;
  token_type: "bearer";
};
