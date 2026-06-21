from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

with open("q-vercel-latency.json") as f:
    DATA = json.load(f)


class RequestBody(BaseModel):
    regions: list[str]
    threshold_ms: int


def percentile(values, p):
    values = sorted(values)

    pos = (len(values) - 1) * p
    lower = int(pos)
    frac = pos - lower

    if lower + 1 < len(values):
        return values[lower] + frac * (
            values[lower + 1] - values[lower]
        )

    return values[lower]


@app.post("/api/latency")
def latency(req: RequestBody):
    result = []

    for region in req.regions:
        rows = [
            r for r in DATA
            if r["region"] == region
        ]

        latencies = [
            r["latency_ms"]
            for r in rows
        ]

        uptimes = [
            r["uptime_pct"]
            for r in rows
        ]

        result.append({
            "region": region,
            "avg_latency": round(
                sum(latencies) / len(latencies),
                2
            ),
            "p95_latency": round(
                percentile(latencies, 0.95),
                2
            ),
            "avg_uptime": round(
                sum(uptimes) / len(uptimes),
                3
            ),
            "breaches": sum(
                1
                for r in rows
                if r["latency_ms"] > req.threshold_ms
            )
        })

    return {"regions": result}
