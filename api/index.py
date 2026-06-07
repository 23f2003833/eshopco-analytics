import json
import os
import statistics
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/q-vercel-latency.json")
with open(DATA_PATH, "r") as f:
    RAW_DATA = json.load(f)

class AnalyticsRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

@app.post("/api/analytics")
def analytics(req: AnalyticsRequest):
    results = {}

    for region in req.regions:
        region_records = [r for r in RAW_DATA if r["region"] == region]

        if not region_records:
            results[region] = None
            continue

        latencies = [r["latency_ms"] for r in region_records]
        uptimes   = [r["uptime_pct"] for r in region_records]

        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)
        p95_index = int(0.95 * n)
        if p95_index >= n:
            p95_index = n - 1

        avg_latency = statistics.mean(latencies)
        p95_latency = sorted_latencies[p95_index]
        avg_uptime  = statistics.mean(uptimes)
        breaches    = sum(1 for l in latencies if l > req.threshold_ms)

        results[region] = {
            "avg_latency": round(avg_latency, 4),
            "p95_latency": round(p95_latency, 4),
            "avg_uptime":  round(avg_uptime, 4),
            "breaches":    breaches,
        }

    return results
