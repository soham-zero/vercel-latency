from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

with open("q-vercel-latency.json", "r") as f:
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


@app.options("/api/latency")
def options():
    response = Response()

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"

    # Important for validator's fetch().headers.get(...)
    response.headers["Access-Control-Expose-Headers"] = (
        "Access-Control-Allow-Origin"
    )

    return response


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

    return JSONResponse(
        content={"regions": result},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Expose-Headers":
                "Access-Control-Allow-Origin"
        }
    )