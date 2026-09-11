import { ReactNode } from "react";

export function Header({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return <header className="page-header"><div><p className="eyebrow">QUALITY OPERATIONS</p><h1>{title}</h1><p>{description}</p></div>{action}</header>;
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) { return <section className={`card ${className}`}>{children}</section>; }
export function Badge({ value }: { value: string }) { return <span className={`badge ${value.toLowerCase().replaceAll(" ", "-")}`}>{value}</span>; }
export function Empty({ children }: { children: ReactNode }) { return <div className="empty">{children}</div>; }
export function ErrorNotice({ message }: { message?: string }) { return message ? <div className="error-notice">{message}</div> : null; }

