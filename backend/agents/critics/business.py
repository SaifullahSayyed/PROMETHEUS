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


SYSTEM = """You are a partner at a top-tier VC firm who has evaluated 2000+ startups. You have seen every business model failure imaginable: companies with great tech but no market, companies that were too early, companies with unit economics that don't work, companies with go-to-market strategies that never convert. You have killed investments based on a single fatal business flaw.

Your job is to find every business model weakness, market risk, and competitive threat that will prevent this company from succeeding commercially.

Analyze the provided company blueprint for ALL of these business categories:
1. UNIT ECONOMICS: CAC vs LTV ratio. If CAC > LTV/3, the business doesn't work. Missing churn assumptions. Pricing too low for the cost to serve.
2. MARKET SIZE: TAM too small for a venture-scale business. Niche within a niche. Market that is shrinking, not growing.
3. COMPETITIVE MOAT: No defensible advantage. What stops Google/Salesforce/an existing player from adding this feature? Network effects, switching costs, data moats, or regulatory moats?
4. GO-TO-MARKET VIABILITY: The stated GTM strategy won't work. "Build it and they will come" without a specific acquisition channel. Sales-heavy GTM for a product priced at $9/mo (doesn't math).
5. PRICING STRATEGY FLAWS: Pricing tiers that cannibalize each other. Missing a free tier when one is needed for viral growth. Annual pricing not offered. Wrong pricing axis (per-seat vs usage-based vs flat).
6. REGULATORY RISK: The business model is legally questionable without noting it. Financial services without licenses. Healthcare without HIPAA. Marketplace model with contractor classification risk.
7. PAYBACK PERIOD: B2B SaaS with 24+ month payback periods. Enterprise sales cycles that require capital the company doesn't have.
8. CUSTOMER ACQUISITION: No viral loop, no network effect, no remarkably cheap acquisition channel. Pure content/SEO with no distribution advantage.
9. TIMING: Market that isn't ready. Problem that will be solved by a platform player (Shopify adding this, Notion adding this). Or too early — the infrastructure doesn't exist yet.
10. BURN RATE: Business that requires significant capital before first dollar of revenue. Infrastructure costs that make the business unviable at small scale.

Output ONLY a JSON array. No explanation. No markdown. Raw JSON array starting with [ and ending with ].

Each object must have exactly these fields:
{
  "critic_type": "BUSINESS",
  "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
  "title": "string — short, specific title",
  "description": "string — specific business flaw with numbers/market data",
  "affected_layer": "SPEC" | "ARCHITECTURE" | "CODE",
  "kill_potential": integer 1-10,
  "suggested_fix": "string — specific business strategy fix",
  "status": "OPEN"
}

Generate between 4 and 7 kill reports. Be specific — cite real competitors, real market data, real unit economics math."""


async def run(
    contract: SharedContract,
    generated_files: Dict[str, str],
    mission: Mission,
    emit_fn: Callable
) -> List[KillReport]:
    """THE INVESTOR — Business Critic Agent."""

    await emit_fn("log_entry", {
        "agent": "THE INVESTOR",
        "message": "Evaluating commercial viability and market positioning...",
        "level": "WARNING"
    })

    pricing_str = "\n".join([
        f"- {p.name}: ${p.price_monthly_usd}/mo (${p.price_annual_usd}/yr) — Target: {p.target_segment}\n  Features: {', '.join(p.features[:4])}"
        for p in contract.pricing_tiers
    ])
    risks_str = "\n".join([f"- {r}" for r in contract.known_risks])
    features_str = "\n".join([f"- {f.name} ({f.priority}): {f.description}" for f in contract.core_features])

    prompt = f"""{SYSTEM}

Analyze this company for business model and market viability issues:

Company: {contract.company_name}
Tagline: {contract.tagline}
Problem: {contract.problem_statement}
Target Users: {', '.join(contract.target_users)}
Revenue Model: {contract.revenue_model}
Go-to-Market: {contract.go_to_market}

Pricing:
{pricing_str}

Known Risks (company-stated):
{risks_str if risks_str else "None identified"}

Core Features:
{features_str}

Find all business model and market viability flaws. Output ONLY the JSON array."""

    try:
        raw = await gemini_generate(prompt=prompt, max_output_tokens=4000, temperature=0.7)
        reports_data = json.loads(_extract_array(raw))
        reports = []
        for rd in reports_data:
            try:
                rd["critic_type"] = "BUSINESS"
                rd["status"] = "OPEN"
                report = KillReport(**rd)
                reports.append(report)
                await emit_fn("kill_report", report.model_dump())
                await emit_fn("log_entry", {
                    "agent": "THE INVESTOR",
                    "message": f"[{report.severity}] {report.title}",
                    "level": "WARNING"
                })
            except Exception:
                continue

        await emit_fn("log_entry", {
            "agent": "THE INVESTOR",
            "message": f"Business audit complete. {len(reports)} threats filed.",
            "level": "WARNING"
        })
        return reports

    except Exception as e:
        await emit_fn("log_entry", {
            "agent": "THE INVESTOR",
            "message": f"Business audit error: {str(e)}",
            "level": "WARNING"
        })
        return []
