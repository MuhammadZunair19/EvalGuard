"use client";

import { BarChart3, Database, FileText, FlaskConical, Gauge, GitCompareArrows, Settings, SlidersHorizontal, TerminalSquare } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const navigation = [
  ["Dashboard", "/", BarChart3], ["Documents", "/documents", FileText],
  ["Datasets", "/datasets", Database], ["Evaluation Runs", "/runs", FlaskConical],
  ["Compare Runs", "/compare", GitCompareArrows], ["Prompt Versions", "/prompts", TerminalSquare],
  ["Quality Gates", "/quality-gates", SlidersHorizontal], ["Settings", "/settings", Settings],
] as const;

export function Sidebar() {
  const path = usePathname();
  return <aside className="sidebar">
    <div className="brand"><span className="brand-mark"><Gauge size={20}/></span><div><strong>EvalGuard</strong><small>AI QUALITY CONTROL</small></div></div>
    <nav>{navigation.map(([label, href, Icon]) => <Link key={href} href={href} className={path === href || (href !== "/" && path.startsWith(href)) ? "active" : ""}><Icon size={18}/><span>{label}</span></Link>)}</nav>
    <div className="environment"><span className="status-dot"/>Local environment<small>Ollama · PostgreSQL</small></div>
  </aside>;
}

