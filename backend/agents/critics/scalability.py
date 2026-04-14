import json
import re
from typing import Dict, List, Callable

from llm import gemini_generate
from models.contract import SharedContract
from models.kill_report import KillReport
from models.mission import Mission


def _extract_array(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:]).strip()
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        return match.group(0)
    return text


SYSTEM = """You are a principal engineer at a hyperscaler who has seen every scalability failure imaginable. You have postmortem reports from Twitter's fail whale, Facebook's cascading failures, Slack's 2019 outage, and GitHub's database incidents. Your job is to find every performance bottleneck, scaling risk, and architecture flaw that will cause this product to fail under load.

You specialize in: database query optimization (N+1 queries, missing indexes), caching strategy, horizontal scaling readiness, single points of failure, API design for throughput, frontend performance, and infrastructure costs at scale.

Analyze the provided company blueprint and code for ALL of these scalability categories:
1. N+1 QUERY PROBLEMS: ORM lazy loading that causes N+1 queries. Missing .select_related() or .prefetch_related(). Queries inside loops.
2. MISSING DATABASE INDEXES: Foreign keys without indexes, columns used in WHERE clauses without indexes, columns used in ORDER BY without indexes.
3. MISSING PAGINATION: Endpoints that return all records without LIMIT/OFFSET or cursor-based pagination. Loading entire tables into memory.
4. SYNCHRONOUS BOTTLENECKS: Long-running operations (email sending, file processing, PDF generation) done inline in request handlers instead of async queues.
5. MISSING CACHING: No Redis/cache layer for frequently-read, rarely-changed data (user profiles, config, static content).
6. SINGLE POINTS OF FAILURE: No database replication or read replicas, single server deployment, no CDN for static assets.
7. MEMORY LEAKS: Loading entire file contents into memory, no streaming for large file operations, WebSocket connections not properly cleaned up.
8. OVER-FETCHING: Returning entire objects when only 2 fields are needed, no GraphQL or field selection.
9. MISSING RATE LIMITING: No circuit breakers on external API calls, no retry with exponential backoff.
10. COST AT SCALE: Infrastructure costs that become prohibitive at 10k, 100k, 1M users. Eg. storing full-resolution images without compression.

Output ONLY a JSON array. No explanation. No markdown. Raw JSON array starting with [ and ending with ].

Each object must have exactly these fields:
{
  "critic_type": "SCALABILITY",
  "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
  "title": "string — short, specific title",
  "description": "string — specific bottleneck description referencing the actual code/schema",
  "affected_layer": "CODE" | "ARCHITECTURE" | "SPEC",
  "kill_potential": integer 1-10,
  "suggested_fix": "string — specific technical fix",
  "status": "OPEN"
}

Generate between 4 and 7 kill reports. Reference specific tables, endpoints, or code patterns found."""


async def run(
    contract: SharedContract,
    generated_files: Dict[str, str],
    mission: Mission,
    emit_fn: Callable
) -> List[KillReport]:
    """THE ARCHITECT — Scalability Critic Agent."""

    await emit_fn("log_entry", {
        "agent": "THE ARCHITECT",
        "message": "Stress-testing architecture for scalability and performance...",
        "level": "WARNING"
    })

    endpoints_str = "\n".join([
        f"- {e.method} {e.path} (auth={e.auth_required}): {e.description}"
        for e in contract.api_endpoints
    ])
    schema_str = "\n".join([
        f"Table {t.name}: " + ", ".join([
            f"{c.name} {c.sql_type} {'PK' if c.primary_key else ''} {'FK→' + c.foreign_key if c.foreign_key else ''} {'IDX' if c.index else ''}"
            for c in t.columns
        ])
        for t in contract.database_schema
    ])
    features_str = "\n".join([f"- {f.name} ({f.priority}): {f.description}" for f in contract.core_features])

    code_sample = ""
    for fname, content in list(generated_files.items())[:4]:
        if fname.endswith(('.py', '.ts', '.tsx', '.js')):
            code_sample += f"\n\n### FILE: {fname}\n{content[:1500]}"

    prompt = f"""{SYSTEM}

Analyze this product for scalability and performance issues:

Company: {contract.company_name}
Tech Stack: {contract.tech_stack.backend} + {contract.tech_stack.frontend} + {contract.tech_stack.database}

API Endpoints (look for missing pagination, over-fetching):
{endpoints_str}

Database Schema (look for missing indexes, FK without indexes):
{schema_str}

Core Features (look for async requirements):
{features_str}

Generated Code Sample:
{code_sample[:4000] if code_sample else "Not available"}

Find all scalability bottlenecks. Output ONLY the JSON array."""

    try:
        raw = await gemini_generate(prompt=prompt, max_output_tokens=4000, temperature=0.6)
        reports_data = json.loads(_extract_array(raw))
        reports = []
        for rd in reports_data:
            try:
                rd["critic_type"] = "SCALABILITY"
                rd["status"] = "OPEN"
                report = KillReport(**rd)
                reports.append(report)
                await emit_fn("kill_report", report.model_dump())
                await emit_fn("log_entry", {
                    "agent": "THE ARCHITECT",
                    "message": f"[{report.severity}] {report.title}",
                    "level": "WARNING"
                })
            except Exception:
                continue

        await emit_fn("log_entry", {
            "agent": "THE ARCHITECT",
            "message": f"Architecture audit complete. {len(reports)} bottlenecks filed.",
            "level": "WARNING"
        })
        return reports

    except Exception as e:
        await emit_fn("log_entry", {
            "agent": "THE ARCHITECT",
            "message": f"Architecture audit error: {str(e)}",
            "level": "WARNING"
        })
        return []
