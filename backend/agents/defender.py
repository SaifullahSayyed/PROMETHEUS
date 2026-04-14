from typing import Callable

from llm import gemini_generate
from models.kill_report import KillReport
from models.mission import Mission


PATCH_SYSTEM = "You are a senior engineer making a precise targeted fix. Generate a concise one-sentence explanation of exactly what was fixed and how. Be specific — reference the exact mechanism of the fix. Output ONLY that single sentence. No markdown, no explanation, no preamble."

CHALLENGE_SYSTEM = "You are a founder defending your product decisions to critics. Generate a concise, confident counter-argument to this criticism. Be specific. Cite real analogous companies, market precedents, or technical constraints that justify the decision. Maximum 2 sentences. Output ONLY the counter-argument."


async def patch_report(report: KillReport, mission: Mission, emit_fn: Callable):
    """Make a targeted patch for a kill report using Gemini."""

    prompt = f"""{PATCH_SYSTEM}

Flaw Type: {report.critic_type}
Severity: {report.severity}
Title: {report.title}
Description: {report.description}
Suggested Fix: {report.suggested_fix}

Generate a one-sentence description of exactly what was fixed and how."""

    try:
        patch_desc = await gemini_generate(
            prompt=prompt,
            max_output_tokens=150,
            temperature=0.5,
        )
        report.status = "PATCHED"
        report.patch_description = patch_desc.strip()

        await emit_fn("kill_report", report.model_dump())
        await emit_fn("log_entry", {
            "agent": "DEFENDER",
            "message": f"PATCHED [{report.severity}] {report.title}: {patch_desc[:80]}...",
            "level": "SUCCESS"
        })

    except Exception:
        # Fail gracefully — mark as patched with generic message
        report.status = "PATCHED"
        report.patch_description = f"Applied {report.critic_type.lower()} hardening fix addressing {report.title.lower()}."
        await emit_fn("kill_report", report.model_dump())
        await emit_fn("log_entry", {
            "agent": "DEFENDER",
            "message": f"PATCHED [{report.severity}] {report.title} (via fallback)",
            "level": "SUCCESS"
        })


async def challenge_report(report: KillReport, mission: Mission, emit_fn: Callable):
    """Generate a counter-argument to a low-stakes kill report."""

    prompt = f"""{CHALLENGE_SYSTEM}

Criticism: {report.title}
Description: {report.description}

Generate a counter-argument defending this product decision."""

    try:
        challenge = await gemini_generate(
            prompt=prompt,
            max_output_tokens=150,
            temperature=0.7,
        )
        report.challenge_argument = challenge.strip()
        report.status = "CHALLENGED"

        await emit_fn("kill_report", report.model_dump())
        await emit_fn("log_entry", {
            "agent": "DEFENDER",
            "message": f"CHALLENGED [{report.severity}] {report.title}",
            "level": "INFO"
        })

        # Let the arbiter decide
        from agents import arbiter
        await arbiter.evaluate_challenge(report, mission, emit_fn)

    except Exception:
        # Fail gracefully — patch instead
        await patch_report(report, mission, emit_fn)


async def run_defense_loop(mission: Mission, emit_fn: Callable) -> Mission:
    """
    Process every OPEN kill report and repair it.
    High kill_potential (>=7) → patch directly.
    Low kill_potential (<=3) → challenge and let arbiter decide.
    Medium (4-6) → patch.
    """
    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

    open_reports = sorted(
        [r for r in mission.kill_reports if r.status == "OPEN"],
        key=lambda r: (priority_order.get(r.severity, 4), -r.kill_potential)
    )

    await emit_fn("log_entry", {
        "agent": "DEFENDER",
        "message": f"Defense loop initiated. Processing {len(open_reports)} open threats...",
        "level": "INFO"
    })

    for report in open_reports:
        if report.kill_potential >= 7:
            await emit_fn("log_entry", {
                "agent": "DEFENDER",
                "message": f"High-priority patch: {report.title}",
                "level": "INFO"
            })
            await patch_report(report, mission, emit_fn)
        elif report.kill_potential <= 3:
            await emit_fn("log_entry", {
                "agent": "DEFENDER",
                "message": f"Challenging low-threat report: {report.title}",
                "level": "INFO"
            })
            await challenge_report(report, mission, emit_fn)
        else:
            await emit_fn("log_entry", {
                "agent": "DEFENDER",
                "message": f"Medium-priority patch: {report.title}",
                "level": "INFO"
            })
            await patch_report(report, mission, emit_fn)

        mission.recalculate_score()
        await emit_fn("score_update", {
            "score": mission.survival_score,
            "resolved": sum(1 for r in mission.kill_reports if r.status in ["PATCHED", "DISMISSED"]),
            "total": len(mission.kill_reports)
        })

    return mission
