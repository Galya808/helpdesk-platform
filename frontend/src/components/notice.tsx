export function Notice({ children, tone = "info" }: { children: React.ReactNode; tone?: "info" | "error" | "success" }) {
  return <div className={`notice notice-${tone}`}>{children}</div>;
}
