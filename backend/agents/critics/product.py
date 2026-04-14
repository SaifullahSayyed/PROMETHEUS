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


SYSTEM = """You are a brutal product manager and UX expert with 12 years of experience at top-tier consumer apps. Your job is to find every product flaw that will cause users to churn, not adopt, or have a terrible experience.

You care about: onboarding friction, missing empty states, dead ends in user flows, confusing navigation, missing mobile responsiveness, lack of social proof, poor error messages, missing notifications and feedback loops, and features that sound good but create more problems than they solve.

Analyze the provided company blueprint for ALL of these UX/product issues:
1. ONBOARDING FRICTION: No guided setup, no starter templates, cold-start problem with empty dashboard.
2. EMPTY STATES: What does the user see before they have any data? Missing zero-state guidance.
3. MISSING CORE INTERACTIONS: Actions that are obvious to users but not built (delete, bulk actions, search, filter, sort, export).
4. NAVIGATION DEAD ENDS: Pages that users can reach but can't escape without using the browser back button.
5. MISSING NOTIFICATIONS: No email confirmations, no activity notifications, no progress indicators.
6. ERROR MESSAGE QUALITY: Generic "Something went wrong" errors with no recovery path.
7. MOBILE EXPERIENCE: Desktop-only interactions that break on mobile.
8. MISSING SOCIAL PROOF: No testimonials, no user count, no activity feeds.
9. MISSING SEARCH AND DISCOVERY: No way to find content in a app with growing data.
10. PRICING PSYCHOLOGY: Pricing tiers that cannibalize each other, missing free trial, no annual discount shown.

Output ONLY a JSON array. No explanation. No markdown. Raw JSON array starting with [ and ending with ].

Each object must have exactly these fields:
{
  "critic_type": "PRODUCT",
  "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
  "title": "string — short, specific title",
  "description": "string — specific to this product",
  "affected_layer": "SPEC" | "CODE" | "ARCHITECTURE",
  "kill_potential": integer 1-10,
  "suggested_fix": "string — specific fix",
  "status": "OPEN"
}

Generate between 4 and 7 kill reports. Be ruthless but specific to this actual product."""


async def run(
    contract: SharedContract,
    generated_files: Dict[str, str],
    mission: Mission,
    emit_fn: Callable
) -> List[KillReport]:
    """THE ADVOCATE — Product Critic Agent."""

    await emit_fn("log_entry", {
        "agent": "THE ADVOCATE",
        "message": "Analyzing user experience and product-market fit...",
        "level": "WARNING"
    })

    features_str = "\n".join([f"- {f.name} ({f.priority}): {f.description}" for f in contract.core_features])
    journeys_str = "\n".join([
        f"- {j.persona}: {' → '.join(j.steps[:4])}"
        for j in contract.user_journeys
    ])
    pricing_str = "\n".join([
        f"- {p.name}: ${p.price_monthly_usd}/mo — {p.target_segment}"
        for p in contract.pricing_tiers
    ])

    prompt = f"""{SYSTEM}

Analyze this product for UX and product flaws:

Company: {contract.company_name}
Tagline: {contract.tagline}
Problem: {contract.problem_statement}
Target Users: {', '.join(contract.target_users)}

Core Features:
{features_str}

User Journeys:
{journeys_str}

Pricing:
{pricing_str}

Find all product and UX issues. Output ONLY the JSON array."""

    try:
        raw = await gemini_generate(prompt=prompt, max_output_tokens=4000, temperature=0.7)
        reports_data = json.loads(_extract_array(raw))
        reports = []
        for rd in reports_data:
            try:
                rd["critic_type"] = "PRODUCT"
                rd["status"] = "OPEN"
                report = KillReport(**rd)
                reports.append(report)
                await emit_fn("kill_report", report.model_dump())
                await emit_fn("log_entry", {
                    "agent": "THE ADVOCATE",
                    "message": f"[{report.severity}] {report.title}",
                    "level": "WARNING"
                })
            except Exception:
                continue

        await emit_fn("log_entry", {
            "agent": "THE ADVOCATE",
            "message": f"Product audit complete. {len(reports)} issues filed.",
            "level": "WARNING"
        })
        return reports

    except Exception as e:
        await emit_fn("log_entry", {
            "agent": "THE ADVOCATE",
            "message": f"Product audit error: {str(e)}",
            "level": "WARNING"
        })
        return []
