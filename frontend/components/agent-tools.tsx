"use client";

import { useEffect } from "react";
import { api } from "@/lib/api";

declare global {
  interface Document {
    readonly modelContext?: {
      registerTool(tool: Record<string, unknown>, options?: { signal?: AbortSignal }): void | Promise<void>;
    };
  }
}

export function AgentTools() {
  useEffect(() => {
    const context = document.modelContext;
    if (!context?.registerTool) return;
    const lifecycle = new AbortController();

    void Promise.resolve(context.registerTool({
      name: "read_quality_dashboard",
      title: "Read quality dashboard",
      description: "Read the current EvalGuard quality posture and recent metric trends.",
      inputSchema: { type: "object", properties: {}, additionalProperties: false },
      annotations: { readOnlyHint: true, untrustedContentHint: false },
      execute: async () => api("/dashboard"),
    }, { signal: lifecycle.signal })).catch(console.error);

    void Promise.resolve(context.registerTool({
      name: "create_evaluation_dataset",
      title: "Create evaluation dataset",
      description: "Create a named EvalGuard dataset and open the dataset authoring screen.",
      inputSchema: {
        type: "object",
        properties: {
          name: { type: "string", minLength: 1 },
          description: { type: "string" },
        },
        required: ["name"],
        additionalProperties: false,
      },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      execute: async (input: unknown) => {
        const value = input as { name?: unknown; description?: unknown };
        if (typeof value.name !== "string" || !value.name.trim()) throw new Error("name is required");
        const dataset = await api<{ id: string; name: string }>("/datasets", {
          method: "POST",
          body: JSON.stringify({ name: value.name.trim(), description: typeof value.description === "string" ? value.description : null }),
        });
        window.location.assign("/datasets");
        return { id: dataset.id, name: dataset.name };
      },
    }, { signal: lifecycle.signal })).catch(console.error);

    return () => lifecycle.abort();
  }, []);

  return null;
}

