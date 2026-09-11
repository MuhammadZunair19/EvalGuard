"use client";

import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function TrendChart({ data }: { data: any[] }) {
  return <div className="chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={data}><CartesianGrid stroke="#282827" vertical={false}/><XAxis dataKey="timestamp" tickFormatter={(v) => new Date(v).toLocaleDateString(undefined, { month: "short", day: "numeric" })} stroke="#73736d" fontSize={12}/><YAxis stroke="#73736d" fontSize={12}/><Tooltip contentStyle={{ background: "#181817", border: "1px solid #343431", borderRadius: 8 }}/><Legend/><Line type="monotone" dataKey="pass_rate" name="Pass rate %" stroke="#f5b942" strokeWidth={2}/><Line type="monotone" dataKey="faithfulness" name="Faithfulness" stroke="#55b89c" strokeWidth={2}/><Line type="monotone" dataKey="answer_relevance" name="Relevance" stroke="#7aa2e3" strokeWidth={2}/></LineChart></ResponsiveContainer></div>;
}

