import type { Metadata } from "next";
import { Sidebar } from "@/components/sidebar";
import "./globals.css";

export const metadata: Metadata = { title: "EvalGuard", description: "AI and RAG quality assurance dashboard", icons: { icon: "/favicon.svg" } };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><Sidebar/><main>{children}</main></body></html>;
}

