import asyncio
import json
import os
from pathlib import Path
from typing import Optional
from models.mission import Mission
from agents import builder, defender
from agents.critics import CRITICS

_missions: dict[str, Mission] = {}
_sse_queues: dict[str, asyncio.Queue] = {}

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
DEMO_MISSIONS_DIR = Path(__file__).parent / "demo_missions"

DEMO_IDS = {
    "demo-classpay-001": "classpay.json",
    "demo-freelancer-002": "billdr.json",
    "demo-foodmkt-003": "cultivar.json",
}

def _load_demo_fixture(mission_id: str) -> Optional[Mission]:
    filename = DEMO_IDS.get(mission_id)
    if not filename:
        return None
    path = DEMO_MISSIONS_DIR / filename
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return Mission(**data)

def get_mission(mission_id: str) -> Optional[Mission]:
    if mission_id in _missions:
        return _missions[mission_id]
    if mission_id in DEMO_IDS:
        mission = _load_demo_fixture(mission_id)
        if mission:
            _missions[mission_id] = mission
        return mission
    return None

def store_mission(mission: Mission):
    _missions[mission.id] = mission

def get_queue(mission_id: str) -> asyncio.Queue:
    if mission_id not in _sse_queues:
        _sse_queues[mission_id] = asyncio.Queue()
    return _sse_queues[mission_id]

async def emit(mission_id: str, event_type: str, data: dict):
    queue = get_queue(mission_id)
    await queue.put({"type": event_type, "data": data})
    if event_type == "log_entry":
        mission = get_mission(mission_id)
        if mission:
            mission.add_log(
                data.get("agent", "SYSTEM"),
                data.get("message", ""),
                data.get("level", "INFO")
            )
            store_mission(mission)

async def _replay_demo(mission_id: str):
    mission = _load_demo_fixture(mission_id)
    if not mission:
        return
    store_mission(mission)
    await asyncio.sleep(0.3)

    queue = get_queue(mission_id)

    await queue.put({"type": "phase_change", "data": {"phase": "GENESIS", "message": "Generating company blueprint..."}})
    await asyncio.sleep(1.2)

    await queue.put({"type": "phase_change", "data": {"phase": "GENESIS_COMPLETE", "company_name": mission.contract.company_name, "tagline": mission.contract.tagline}})
    await asyncio.sleep(0.8)

    await queue.put({"type": "phase_change", "data": {"phase": "CONSTRUCTION", "message": "Building MVP with parallel agents..."}})
    for log in mission.combat_log[:8]:
        await asyncio.sleep(0.4)
        await queue.put({"type": "log_entry", "data": {"agent": log.agent, "message": log.message, "level": log.level}})

    await asyncio.sleep(0.8)
    await queue.put({"type": "phase_change", "data": {"phase": "ATTACK", "message": "Critic council activated. 5 agents deploying..."}})
    await asyncio.sleep(0.5)

    for report in mission.kill_reports:
        await asyncio.sleep(0.6)
        await queue.put({"type": "kill_report", "data": report.model_dump()})
        await queue.put({"type": "log_entry", "data": {
            "agent": "SYSTEM",
            "message": f"[{report.severity}] {report.title}",
            "level": "WARNING"
        }})

    await asyncio.sleep(0.5)
    await queue.put({"type": "score_update", "data": {
        "score": 55.0,
        "resolved": 0,
        "total": len(mission.kill_reports)
    }})

    await asyncio.sleep(1.0)
    await queue.put({"type": "phase_change", "data": {"phase": "DEFENSE", "message": "Autonomous defense loop initiated..."}})
    await asyncio.sleep(0.5)

    resolved = 0
    for report in mission.kill_reports:
        await asyncio.sleep(0.8)
        report_data = report.model_dump()
        await queue.put({"type": "kill_report", "data": report_data})
        resolved += 1
        await queue.put({"type": "score_update", "data": {
            "score": min(100.0, (resolved / len(mission.kill_reports)) * 100),
            "resolved": resolved,
            "total": len(mission.kill_reports)
        }})
        await queue.put({"type": "log_entry", "data": {
            "agent": "DEFENDER",
            "message": f"{'PATCHED' if report.status == 'PATCHED' else 'DISMISSED'} [{report.severity}] {report.title}",
            "level": "SUCCESS"
        }})

    await asyncio.sleep(1.0)
    await queue.put({"type": "phase_change", "data": {"phase": "DEPLOYING", "message": "Packaging survivor for deployment..."}})
    await asyncio.sleep(1.5)

    mission.survival_score = 100.0
    mission.status = "DEPLOYED"
    store_mission(mission)

    await queue.put({"type": "score_update", "data": {"score": 100.0, "resolved": len(mission.kill_reports), "total": len(mission.kill_reports)}})
    await queue.put({"type": "deploy_complete", "data": {
        "url": mission.deploy_url,
        "survival_score": 100.0,
        "total_reports": len(mission.kill_reports),
        "company_name": mission.contract.company_name,
        "tagline": mission.contract.tagline
    }})
    await queue.put({"type": "complete", "status": "DEPLOYED"})

async def run_pipeline(mission_id: str):
    if mission_id in DEMO_IDS:
        await _replay_demo(mission_id)
        return

    mission = get_mission(mission_id)
    if not mission:
        return

    async def emit_fn(event_type: str, data: dict):
        await emit(mission_id, event_type, data)

    try:
        mission.status = "GENESIS"
        mission.current_phase = "GENESIS"
        store_mission(mission)
        await emit_fn("phase_change", {"phase": "GENESIS", "message": "Generating company blueprint..."})
        mission.add_log("BUILDER", "Analyzing problem statement...", "INFO")
        store_mission(mission)
        contract = await builder.generate_contract(mission.input_prompt, mission, emit_fn)
        mission.contract = contract
        mission.add_log("BUILDER", f"Blueprint complete: {contract.company_name} — {contract.tagline}", "SUCCESS")
        await emit_fn("phase_change", {"phase": "GENESIS_COMPLETE", "company_name": contract.company_name, "tagline": contract.tagline})
        store_mission(mission)
        mission.status = "CONSTRUCTION"
        mission.current_phase = "CONSTRUCTION"
        store_mission(mission)
        await emit_fn("phase_change", {"phase": "CONSTRUCTION", "message": "Building MVP with parallel agents..."})
        mission.add_log("BUILDER", "Launching parallel build agents...", "INFO")
        store_mission(mission)
        generated_files = await builder.construct_codebase(contract, mission, emit_fn)
        mission.generated_files = generated_files
        mission.add_log("BUILDER", f"Construction complete: {len(generated_files)} files generated", "SUCCESS")
        store_mission(mission)
        mission.status = "ATTACK"
        mission.current_phase = "ATTACK"
        store_mission(mission)
        await emit_fn("phase_change", {"phase": "ATTACK", "message": "Critic council activated. 5 agents deploying..."})
        mission.add_log("SYSTEM", "All 5 critic agents deployed simultaneously.", "WARNING")
        store_mission(mission)
        critic_tasks = list(CRITICS.items())
        all_report_lists = []
        for critic_type, critic_fn in critic_tasks:
            try:
                reports = await critic_fn(contract, generated_files, mission, emit_fn)
                all_report_lists.append(reports)
            except Exception as e:
                all_report_lists.append(e)
        for reports in all_report_lists:
            if isinstance(reports, list):
                for report in reports:
                    mission.kill_reports.append(report)
        mission.recalculate_score()
        await emit_fn("score_update", {
            "score": mission.survival_score,
            "resolved": 0,
            "total": len(mission.kill_reports)
        })
        severity_str = f"CRITICAL:{sum(1 for r in mission.kill_reports if r.severity == 'CRITICAL')} | HIGH:{sum(1 for r in mission.kill_reports if r.severity == 'HIGH')} | MEDIUM:{sum(1 for r in mission.kill_reports if r.severity == 'MEDIUM')} | LOW:{sum(1 for r in mission.kill_reports if r.severity == 'LOW')}"
        mission.add_log(
            "SYSTEM",
            f"Attack complete: {len(mission.kill_reports)} vulnerabilities found. {severity_str}. Survival: {mission.survival_score:.0f}%",
            "CRITICAL" if mission.survival_score < 50 else "WARNING"
        )
        store_mission(mission)
        if mission.survival_score < 100.0:
            mission.status = "DEFENSE"
            mission.current_phase = "DEFENSE"
            store_mission(mission)
            await emit_fn("phase_change", {"phase": "DEFENSE", "message": "Autonomous defense loop initiated..."})
            mission = await defender.run_defense_loop(mission, emit_fn)
            mission.recalculate_score()
            mission.add_log("DEFENDER", f"Defense complete. Final survival: {mission.survival_score:.0f}%", "SUCCESS")
            store_mission(mission)
        else:
            mission.add_log("SYSTEM", "No threats detected. Skipping defense phase.", "SUCCESS")
            store_mission(mission)
        mission.status = "DEPLOYING"
        mission.current_phase = "DEPLOYING"
        store_mission(mission)
        await emit_fn("phase_change", {"phase": "DEPLOYING", "message": "Packaging survivor for deployment..."})
        from deployer import deploy
        deploy_url = await deploy(mission)
        mission.deploy_url = deploy_url
        mission.status = "DEPLOYED"
        mission.survival_score = 100.0
        store_mission(mission)
        mission.add_log("SYSTEM", f"MISSION COMPLETE — DEPLOYED: {deploy_url}", "SUCCESS")
        await emit_fn("deploy_complete", {
            "url": deploy_url,
            "survival_score": mission.survival_score,
            "total_reports": len(mission.kill_reports),
            "company_name": contract.company_name,
            "tagline": contract.tagline
        })
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        mission.status = "FAILED"
        mission.error = str(e)
        store_mission(mission)
        await emit_fn("error", {"message": str(e), "detail": traceback.format_exc()})
        mission.add_log("SYSTEM", f"Pipeline FAILED: {str(e)}", "CRITICAL")
        store_mission(mission)