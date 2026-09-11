"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";

import { Badge, Card, Empty, ErrorNotice, Header } from "@/components/ui";
import { api } from "@/lib/api";
import { Dataset, Run } from "@/lib/types";

type PromptVersion = { id: string; name: string; version: number };

export default function RunsPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [prompts, setPrompts] = useState<PromptVersion[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = () =>
    Promise.all([
      api<Run[]>("/evaluation-runs"),
      api<Dataset[]>("/datasets"),
      api<PromptVersion[]>("/prompts"),
    ])
      .then(([runItems, datasetItems, promptItems]) => {
        setRuns(runItems);
        setDatasets(datasetItems);
        setPrompts(promptItems);
      })
      .catch((reason) => setError(reason.message));

  useEffect(() => {
    void load();
  }, []);

  async function executeRun(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const promptVersion = String(form.get("prompt_version") ?? "");
    setBusy(true);
    try {
      await api("/evaluation-runs", {
        method: "POST",
        body: JSON.stringify({
          dataset_id: form.get("dataset"),
          prompt_version_id: promptVersion || null,
          top_k: Number(form.get("top_k")),
          model: form.get("model"),
        }),
      });
      await load();
    } catch (reason: any) {
      setError(reason.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Header
        title="Evaluation runs"
        description="Execute suites and investigate AI quality failures with stored evidence."
      />
      <ErrorNotice message={error} />
      <Card>
        <form className="toolbar" onSubmit={executeRun}>
          <select name="dataset" aria-label="Evaluation dataset" required>
            <option value="">Select dataset</option>
            {datasets.map((dataset) => (
              <option key={dataset.id} value={dataset.id}>
                {dataset.name}
              </option>
            ))}
          </select>
          <select name="prompt_version" aria-label="Prompt version">
            <option value="">Default grounded prompt</option>
            {prompts.map((prompt) => (
              <option key={prompt.id} value={prompt.id}>
                {prompt.name} · v{prompt.version}
              </option>
            ))}
          </select>
          <input aria-label="Model" name="model" defaultValue="llama3.1:8b" />
          <input
            aria-label="Top K"
            name="top_k"
            type="number"
            min="1"
            max="20"
            defaultValue="5"
          />
          <button className="button" disabled={busy}>
            {busy ? "Evaluating…" : "Run evaluation"}
          </button>
        </form>
      </Card>
      <Card>
        <div className="card-title">
          <h2>Run history</h2>
        </div>
        {runs.length ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Run</th>
                  <th>Status</th>
                  <th>Model</th>
                  <th>Tests</th>
                  <th>Pass rate</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr key={run.id}>
                    <td>
                      <Link className="accent mono" href={`/runs/${run.id}`}>
                        {run.id.slice(0, 8)}
                      </Link>
                    </td>
                    <td>
                      <Badge value={run.status} />
                    </td>
                    <td>{run.model}</td>
                    <td>{run.test_count}</td>
                    <td>{run.pass_percentage.toFixed(1)}%</td>
                    <td className="muted">{new Date(run.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty>No evaluation runs recorded.</Empty>
        )}
      </Card>
    </>
  );
}

