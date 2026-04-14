import json
import re
from typing import Callable

from llm import gemini_generate
from models.kill_report import KillReport
from models.mission import Mission


SYSTEM = """You are a neutral technical judge and seasoned startup advisor. A critic found a flaw in a product. The founder challenged it with a counter-argument. Decide objectively whether the criticism is valid or whether the founder's counter-argument holds up.

ACCEPTED means the founder's counter-argument is compelling and the report can be dismissed. This is appropriate when:
- The founder cites a real precedent (Slack, Linear, or Stripe made the same choice)
- The criticism is based on a misunderstanding of the product scope
- The risk is theoretical and not a real user-facing problem
- The trade-off described is intentional and well-reasoned

REJECTED means the flaw is real and must be fixed. This is appropriate when:
- The criticism identifies a real security, legal, or business risk regardless of the counter-argument
- The founder's counter-argument is defensive rather than substantive
- The counter-argument describes future plans rather than current state

Output ONLY a JSON object: {"verdict": "ACCEPTED" or "REJECTED", "reasoning": "one sentence"}. No markdown. No explanation. Raw JSON only."""


async def evaluate_challenge(report: KillReport, mission: Mission, emit_fn: Callable) -> KillReport:
    """
    Neutral arbiter that evaluates a founder's challenge to a critic's kill report.
    ACCEPTED = challenge succeeds → report DISMISSED.
    REJECTED = flaw is real → report stays OPEN, gets patched.
    """

    prompt = f"""{SYSTEM}

Critic Finding:
Title: {report.title}
Description: {report.description}
Severity: {report.severity}
Kill Potential: {report.kill_potential}/10

Founder's Counter-Argument:
{report.challenge_argument}

Decide: is this criticism valid (REJECTED) or does the counter-argument hold up (ACCEPTED)?
Output ONLY JSON: {{"verdict": "ACCEPTED" or "REJECTED", "reasoning": "string"}}"""

    try:
        raw = await gemini_generate(
            prompt=prompt,
            max_output_tokens=200,
            temperature=0.3,
        )
        # Clean up response
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            raw = match.group(0)

        verdict_data = json.loads(raw)
        verdict = verdict_data.get("verdict", "REJECTED").upper()
        reasoning = verdict_data.get("reasoning", "No reasoning provided.")

        report.arbiter_verdict = verdict

        if verdict == "ACCEPTED":
            report.status = "DISMISSED"
            await emit_fn("kill_report", report.model_dump())
            await emit_fn("log_entry", {
                "agent": "ARBITER",
                "message": f"DISMISSED: {report.title} — {reasoning}",
                "level": "INFO"
            })
        else:
            # REJECTED — flaw is real, must patch
            report.status = "OPEN"
            await emit_fn("kill_report", report.model_dump())
            await emit_fn("log_entry", {
                "agent": "ARBITER",
                "message": f"CHALLENGE REJECTED: {report.title} — {reasoning}. Routing to patch.",
                "level": "CRITICAL"
            })
            from agents.defender import patch_report
            await patch_report(report, mission, emit_fn)

    except Exception as e:
        # Fall back to REJECTED and patch
        report.status = "OPEN"
        report.arbiter_verdict = "REJECTED"
        await emit_fn("log_entry", {
            "agent": "ARBITER",
            "message": f"Arbiter error ({str(e)}). Defaulting to patch.",
            "level": "WARNING"
        })
        from agents.defender import patch_report
        await patch_report(report, mission, emit_fn)

    return report
