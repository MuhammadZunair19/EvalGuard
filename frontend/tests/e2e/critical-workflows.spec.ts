import { expect, Page, test } from "@playwright/test";

async function mockApi(page: Page) {
  const datasets = [{ id: "dataset-1", name: "Employee Handbook QA", description: "Policy regression suite", created_at: new Date().toISOString() }];
  const runs = [{ id: "run-current-0001", dataset_id: "dataset-1", model: "llama3.1:8b", status: "failed", test_count: 25, pass_count: 23, fail_count: 2, pass_percentage: 92, summary: { faithfulness: .91, hit_rate: .96, hallucination_rate: .04, latency: { p95: 1180 } }, created_at: new Date().toISOString() }];
  await page.route("http://localhost:8000/api/v1/**", async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/health")) return route.fulfill({ json: { status: "healthy", service: "evalguard-api", ollama_model: "llama3.2:3b", provider_mode: "local", default_top_k: 2 } });
    if (path.endsWith("/dashboard")) return route.fulfill({ json: { total_runs: 4, latest_pass_rate: 92, ai_quality_score: .9, hallucination_rate: .04, retrieval_hit_rate: .96, p95_latency_ms: 1180, trends: [{ id: "1", timestamp: new Date().toISOString(), pass_rate: 92, faithfulness: .91, answer_relevance: .89, hallucination_rate: .04, p95_latency_ms: 1180 }] } });
    if (path.endsWith("/documents") && route.request().method() === "GET") return route.fulfill({ json: [{ id: "doc-1", filename: "employee_handbook.md", file_type: "md", created_at: new Date().toISOString(), chunk_count: 4, indexing_status: "indexed" }] });
    if (path.endsWith("/datasets")) return route.fulfill({ status: route.request().method() === "POST" ? 201 : 200, json: datasets });
    if (path.endsWith("/evaluation-runs")) return route.fulfill({ status: route.request().method() === "POST" ? 201 : 200, json: route.request().method() === "POST" ? runs[0] : runs });
    if (path.includes("/evaluation-runs/run-current-0001/results")) return route.fulfill({ json: { run: { ...runs[0], pass_percentage: 92 }, failure_breakdown: { Hallucination: 1 }, results: [{ id: "result-1", question: "What is the CEO's daughter's name?", passed: false, failure_type: "Hallucination", latency_ms: 220, expected_answer: null, actual_answer: "The CEO's daughter is Sarah.", retrieved_context: [], unsupported_claims: ["The CEO's daughter is Sarah."], metrics: [{ metric: "hallucination", score: 1, threshold: .05, passed: false }] }] } });
    return route.fulfill({ status: 200, json: [] });
  });
}

test.beforeEach(async ({ page }) => mockApi(page));

test("dashboard exposes live quality posture", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Quality overview" })).toBeVisible();
  await expect(page.getByText("92.0%").first()).toBeVisible();
  await expect(page.getByText("1180 ms")).toBeVisible();
});

test("document inventory shows indexed sources", async ({ page }) => {
  await page.goto("/documents");
  await expect(page.getByText("employee_handbook.md")).toBeVisible();
  await expect(page.getByText("indexed")).toBeVisible();
});

test("creates a dataset through the critical authoring flow", async ({ page }) => {
  await page.goto("/datasets");
  await page.getByLabel("Name").fill("Release candidate QA");
  await page.getByRole("button", { name: "Create dataset" }).click();
  await expect(page.getByRole("button", { name: "Employee Handbook QA" })).toBeVisible();
});

test("executes an evaluation and inspects a hallucination", async ({ page }) => {
  await page.goto("/runs");
  await expect(page.getByLabel("Model")).toHaveValue("llama3.2:3b");
  await expect(page.getByLabel("Top K")).toHaveValue("2");
  await page.getByRole("combobox").first().selectOption("dataset-1");
  await page.getByRole("button", { name: "Run evaluation" }).click();
  await page.getByRole("link", { name: "run-curr" }).click();
  await expect(page.getByText("What is the CEO's daughter's name?")).toBeVisible();
  await expect(page.locator(".badge", { hasText: "Hallucination" })).toBeVisible();
});
