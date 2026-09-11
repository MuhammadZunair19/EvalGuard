export type Dashboard = {
  total_runs: number; latest_pass_rate: number; ai_quality_score: number;
  hallucination_rate: number; retrieval_hit_rate: number; p95_latency_ms: number;
  trends: Array<{ id: string; timestamp: string; pass_rate: number; faithfulness: number; answer_relevance: number; hallucination_rate: number; p95_latency_ms: number }>;
};

export type Document = { id: string; filename: string; file_type: string; created_at: string; chunk_count: number; indexing_status: string };
export type Dataset = { id: string; name: string; description?: string; created_at: string };
export type Run = { id: string; dataset_id: string; model: string; status: string; test_count: number; pass_count: number; fail_count: number; pass_percentage: number; summary: Record<string, any>; created_at: string };

