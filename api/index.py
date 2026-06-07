import json
import os
import statistics
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/q-vercel-latency.json")
with open(DATA_PATH, "r") as f:
    RAW_DATA = json.load(f)

class AnalyticsRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

def compute(req: AnalyticsRequest):
    results = {}
    for region in req.regions:
        region_records = [r for r in RAW_DATA if r["region"] == region]
        if not region_records:
            results[region] = None
            continue
        latencies = [r["latency_ms"] for r in region_records]
        uptimes = [r["uptime_pct"] for r in region_records]
        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)
        p95_index = min(int(0.95 * n), n - 1)
        results[region] = {
            "avg_latency": round(statistics.mean(latencies), 4),
            "p95_latency": round(sorted_latencies[p95_index], 4),
            "avg_uptime": round(statistics.mean(uptimes), 4),
            "breaches": sum(1 for l in latencies if l > req.threshold_ms),
        }
    return {"regions": results}

@app.post("/")
def root(req: AnalyticsRequest):
    return JSONResponse(content=compute(req), headers={"Access-Control-Allow-Origin": "*"})

@app.post("/api/analytics")
def analytics(req: AnalyticsRequest):
    return JSONResponse(content=compute(req), headers={"Access-Control-Allow-Origin": "*"})