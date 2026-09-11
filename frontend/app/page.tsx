"use client";

import { useEffect, useState } from "react";
import { Activity, BrainCircuit, Clock3, DatabaseZap, FlaskConical, ShieldAlert } from "lucide-react";
import { TrendChart } from "@/components/trend-chart";
import { Card, Empty, ErrorNotice, Header } from "@/components/ui";
import { api } from "@/lib/api";
import { Dashboard } from "@/lib/types";

const formatPercent = (value: number) => `${(value <= 1 ? value * 100 : value).toFixed(1)}%`;

export default function DashboardPage() {
  const [data, setData] = useState<Dashboard>(); const [error, setError] = useState("");
  useEffect(() => { api<Dashboard>("/dashboard").then(setData).catch((e) => setError(e.message)); }, []);
  const cards = data ? [["Total test runs", data.total_runs, FlaskConical], ["Latest pass rate", formatPercent(data.latest_pass_rate), Activity], ["AI quality score", formatPercent(data.ai_quality_score), BrainCircuit], ["Hallucination rate", formatPercent(data.hallucination_rate), ShieldAlert], ["Retrieval hit rate", formatPercent(data.retrieval_hit_rate), DatabaseZap], ["P95 latency", `${data.p95_latency_ms.toFixed(0)} ms`, Clock3]] as const : [];
  return <><Header title="Quality overview" description="Release confidence across retrieval, generation, grounding, and performance."/><ErrorNotice message={error}/><div className="grid kpis">{cards.map(([label,value,Icon])=><Card key={label} className="kpi"><Icon size={17} className="muted"/><span>{label}</span><strong>{value}</strong></Card>)}</div><div className="grid section-grid"><Card><div className="card-title"><h2>Quality trend</h2><span className="muted">Last 12 runs</span></div>{data?.trends.length ? <TrendChart data={data.trends}/> : <Empty>Run an evaluation suite to establish a quality baseline.</Empty>}</Card><Card><div className="card-title"><h2>Latest gate posture</h2></div><div className="metric-list">{[["Faithfulness",data?.trends.at(-1)?.faithfulness],["Answer relevance",data?.trends.at(-1)?.answer_relevance],["Retrieval hit rate",data?.retrieval_hit_rate]].map(([label,value])=><div className="metric-row" key={String(label)}><label>{label}</label><span className="mono">{formatPercent(Number(value??0))}</span><div className="track"><div className="fill" style={{width:formatPercent(Number(value??0))}}/></div></div>)}</div></Card></div></>;
}

