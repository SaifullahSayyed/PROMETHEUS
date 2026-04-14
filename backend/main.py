import asyncio
import json
import os
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv(override=True)
from models.mission import Mission
from graph import run_pipeline, get_mission, store_mission, get_queue, emit, _missions, DEMO_MODE, DEMO_IDS
app = FastAPI(title="Prometheus API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://*.vercel.app",
        os.getenv("CORS_ORIGINS", "http://localhost:3000"),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class CreateMissionRequest(BaseModel):
    prompt: str
@app.post("/api/missions")
async def create_mission(request: CreateMissionRequest, background_tasks: BackgroundTasks):
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    mission = Mission(input_prompt=request.prompt.strip())
    mission.add_log("SYSTEM", "Mission created. Initiating Prometheus pipeline.", "INFO")
    store_mission(mission)
    get_queue(mission.id)
    background_tasks.add_task(run_pipeline, mission.id)
    return {"mission_id": mission.id, "status": "PENDING"}
@app.post("/api/demo/{demo_index}")
async def launch_demo(demo_index: int, background_tasks: BackgroundTasks):
    demo_ids = list(DEMO_IDS.keys())
    if demo_index < 0 or demo_index >= len(demo_ids):
        raise HTTPException(status_code=404, detail="Demo not found")
    mission_id = demo_ids[demo_index]
    get_queue(mission_id)
    background_tasks.add_task(run_pipeline, mission_id)
    return {"mission_id": mission_id, "status": "PENDING", "demo": True}
@app.get("/api/missions/{mission_id}/stream")
async def stream_mission(mission_id: str):
    mission = get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    async def event_generator() -> AsyncGenerator[str, None]:
        queue = get_queue(mission_id)
        terminal_statuses = {"DEPLOYED", "FAILED"}
        current = get_mission(mission_id)
        if current:
            yield f"data: {json.dumps({'type': 'init', 'data': current.model_dump()})}\n\n"
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=25.0)
                yield f"data: {json.dumps(event)}\n\n"
                current = get_mission(mission_id)
                if current and current.status in terminal_statuses:
                    while not queue.empty():
                        try:
                            remaining = queue.get_nowait()
                            yield f"data: {json.dumps(remaining)}\n\n"
                        except Exception:
                            break
                    yield f"data: {json.dumps({'type': 'complete', 'status': current.status})}\n\n"
                    break
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"
                current = get_mission(mission_id)
                if current and current.status in terminal_statuses:
                    yield f"data: {json.dumps({'type': 'complete', 'status': current.status})}\n\n"
                    break
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'data': {'message': str(e)}})}\n\n"
                break
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )
@app.get("/api/missions/{mission_id}")
async def get_mission_endpoint(mission_id: str):
    mission = get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission.model_dump()
@app.get("/api/missions/{mission_id}/files")
async def get_mission_files(mission_id: str):
    mission = get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return {"files": mission.generated_files}
@app.get("/preview/{mission_id}", response_class=HTMLResponse)
async def preview_mission(mission_id: str):
    mission = get_mission(mission_id)
    if not mission:
        return HTMLResponse("<h1>Mission not found</h1>", status_code=404)
    contract = mission.contract
    company_name = contract.company_name if contract else "Generated Company"
    tagline = contract.tagline if contract else ""
    features = contract.core_features[:6] if contract else []
    pricing = contract.pricing_tiers if contract else []
    features_html = "".join([
        f"""<div class='feature'>
            <div class='feature-icon'>{'★' if f.priority == 'P0' else '◆' if f.priority == 'P1' else '●'}</div>
            <h3>{f.name}</h3>
            <p>{f.description}</p>
            <span class='priority'>{f.priority}</span>
        </div>"""
        for f in features
    ])
    pricing_html = "".join([
        f"""<div class='pricing-card {'featured' if i == 1 else ''}'>
            <div class='tier-name'>{p.name}</div>
            <div class='price'><span class='amount'>${p.price_monthly_usd:.0f}</span><span class='period'>/mo</span></div>
            <div class='annual'>${p.price_annual_usd:.0f}/yr billed annually</div>
            <ul>{''.join(f"<li>{feat}</li>" for feat in p.features[:5])}</ul>
            <a href='#' class='tier-cta'>Get Started</a>
        </div>"""
        for i, p in enumerate(pricing[:3])
    ])
    stats_html = f"""
        <div class='stat'><span class='stat-num'>{len(mission.kill_reports)}</span><span class='stat-label'>Attacks Survived</span></div>
        <div class='stat'><span class='stat-num'>{mission.survival_score:.0f}%</span><span class='stat-label'>Survival Score</span></div>
        <div class='stat'><span class='stat-num'>{len(mission.generated_files)}</span><span class='stat-label'>Files Generated</span></div>
    """
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en">
<head>
<title>{company_name} — Built by PROMETHEUS</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{tagline}">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*, *::before, *::after {  margin:0; padding:0; box-sizing:border-box; } 
:root { 
  --bg: #080810;
  --surface: #0f0f1a;
  --surface2: #161625;
  --border: #1e1e35;
  --green: #00ff88;
  --green-dim: rgba(0,255,136,0.15);
  --blue: #4488ff;
  --text: #e8eaf0;
  --muted: #6b7280;
  --accent: #7c3aed;
} 
body {  font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; } 
a {  color: inherit; text-decoration: none; } 
/* NAV */
nav {  position: fixed; top: 0; left: 0; right: 0; z-index: 100; background: rgba(8,8,16,0.85); backdrop-filter: blur(12px); border-bottom: 1px solid var(--border); padding: 16px 40px; display: flex; align-items: center; justify-content: space-between; } 
.nav-logo {  font-size: 20px; font-weight: 800; background: linear-gradient(135deg, var(--green), var(--blue)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; } 
.nav-links {  display: flex; gap: 32px; font-size: 14px; color: var(--muted); } 
.nav-links a:hover {  color: var(--text); } 
.nav-cta {  background: var(--green); color: #080810; padding: 8px 20px; border-radius: 6px; font-size: 14px; font-weight: 600; } 
.nav-cta:hover {  opacity: 0.9; } 
/* HERO */
.hero {  min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 120px 24px 80px; text-align: center; background: radial-gradient(ellipse 80% 60% at 50% -20%, rgba(0,255,136,0.08), transparent), radial-gradient(ellipse 60% 40% at 80% 80%, rgba(68,136,255,0.06), transparent); } 
.hero-badge {  display: inline-flex; align-items: center; gap: 8px; background: var(--green-dim); border: 1px solid rgba(0,255,136,0.3); color: var(--green); font-size: 12px; font-weight: 500; padding: 6px 16px; border-radius: 20px; margin-bottom: 32px; } 
.hero-badge::before {  content: '●'; font-size: 8px; animation: pulse 2s ease-in-out infinite; } 
@keyframes pulse {  0%,100%{  opacity:1; }  50%{  opacity:0.3; }  } 
h1 {  font-size: clamp(40px, 7vw, 88px); font-weight: 800; line-height: 1.05; margin-bottom: 24px; letter-spacing: -2px; } 
h1 span {  background: linear-gradient(135deg, var(--green), var(--blue)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; } 
.hero-sub {  font-size: clamp(16px, 2.5vw, 20px); color: var(--muted); max-width: 640px; margin-bottom: 48px; line-height: 1.7; } 
.hero-cta {  display: flex; gap: 16px; flex-wrap: wrap; justify-content: center; } 
.btn-primary {  background: var(--green); color: #080810; padding: 16px 36px; border-radius: 8px; font-weight: 700; font-size: 16px; transition: all 0.2s; } 
.btn-primary:hover {  transform: translateY(-2px); box-shadow: 0 8px 30px rgba(0,255,136,0.3); } 
.btn-secondary {  background: transparent; color: var(--text); padding: 16px 36px; border-radius: 8px; font-weight: 500; font-size: 16px; border: 1px solid var(--border); transition: all 0.2s; } 
.btn-secondary:hover {  border-color: var(--green); color: var(--green); } 
/* STATS */
.stats-bar {  display: flex; justify-content: center; gap: 60px; padding: 40px 24px; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); background: var(--surface); } 
.stat {  text-align: center; } 
.stat-num {  display: block; font-size: 36px; font-weight: 800; background: linear-gradient(135deg, var(--green), var(--blue)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; } 
.stat-label {  font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; } 
/* FEATURES */
section {  padding: 80px 24px; max-width: 1100px; margin: 0 auto; } 
.section-label {  font-size: 12px; font-weight: 600; color: var(--green); text-transform: uppercase; letter-spacing: 3px; margin-bottom: 16px; } 
.section-title {  font-size: clamp(28px, 4vw, 44px); font-weight: 800; margin-bottom: 16px; letter-spacing: -1px; } 
.section-sub {  color: var(--muted); font-size: 18px; margin-bottom: 60px; } 
.features-grid {  display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; } 
.feature {  background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 28px; transition: all 0.2s; } 
.feature:hover {  border-color: rgba(0,255,136,0.3); transform: translateY(-2px); } 
.feature-icon {  font-size: 24px; margin-bottom: 16px; color: var(--green); } 
.feature h3 {  font-size: 16px; font-weight: 700; margin-bottom: 8px; } 
.feature p {  font-size: 14px; color: var(--muted); line-height: 1.6; } 
.priority {  display: inline-block; margin-top: 12px; font-size: 10px; font-weight: 600; color: var(--green); background: var(--green-dim); padding: 2px 8px; border-radius: 4px; } 
/* PRICING */
.pricing-section {  background: var(--surface); border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); } 
.pricing-inner {  max-width: 1100px; margin: 0 auto; padding: 80px 24px; } 
.pricing-grid {  display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 20px; } 
.pricing-card {  background: var(--bg); border: 1px solid var(--border); border-radius: 16px; padding: 36px; transition: all 0.2s; } 
.pricing-card.featured {  border-color: var(--green); background: linear-gradient(135deg, var(--bg), rgba(0,255,136,0.03)); position: relative; } 
.pricing-card.featured::before {  content: 'MOST POPULAR'; position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: var(--green); color: #080810; font-size: 10px; font-weight: 700; padding: 4px 14px; border-radius: 20px; } 
.tier-name {  font-size: 14px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px; } 
.price {  font-size: 48px; font-weight: 800; margin-bottom: 4px; } 
.amount {  background: linear-gradient(135deg, var(--text), #a0a0be); -webkit-background-clip: text; -webkit-text-fill-color: transparent; } 
.period {  font-size: 18px; color: var(--muted); font-weight: 400; } 
.annual {  font-size: 13px; color: var(--muted); margin-bottom: 24px; } 
.pricing-card ul {  list-style: none; margin-bottom: 32px; } 
.pricing-card li {  font-size: 14px; color: var(--muted); padding: 6px 0; border-bottom: 1px solid var(--border); } 
.pricing-card li::before {  content: '✓ '; color: var(--green); font-weight: 700; } 
.tier-cta {  display: block; text-align: center; padding: 14px; border-radius: 8px; font-weight: 600; font-size: 15px; transition: all 0.2s; border: 1px solid var(--border); color: var(--text); } 
.featured .tier-cta {  background: var(--green); color: #080810; border-color: var(--green); } 
.tier-cta:hover {  transform: translateY(-2px); } 
/* FOOTER */
footer {  padding: 48px 24px; text-align: center; border-top: 1px solid var(--border); } 
.prometheus-badge {  display: inline-flex; align-items: center; gap: 12px; background: var(--surface2); border: 1px solid var(--border); border-radius: 8px; padding: 12px 20px; font-size: 12px; color: var(--muted); } 
.prometheus-badge strong {  color: var(--green); } 
footer p {  margin-top: 16px; font-size: 13px; color: var(--muted); } 
@media(max-width:768px) { 
  nav {  padding: 12px 20px; } 
  .nav-links {  display: none; } 
  .stats-bar {  gap: 30px; flex-wrap: wrap; } 
  h1 {  letter-spacing: -1px; } 
} 
</style>
</head>
<body>
<nav>
  <div class="nav-logo">{company_name}</div>
  <div class="nav-links">
    <a href="#features">Features</a>
    <a href="#pricing">Pricing</a>
    <a href="#">Docs</a>
  </div>
  <a href="#" class="nav-cta">Get Started Free</a>
</nav>
<div class="hero">
  <div class="hero-badge">Built &amp; Battle-Tested by PROMETHEUS AI</div>
  <h1>{company_name}<br><span>{tagline.split(' — ')[0] if ' — ' in tagline else tagline[:40]}</span></h1>
  <p class="hero-sub">{tagline}</p>
  <div class="hero-cta">
    <a href="#" class="btn-primary">Start Free Trial →</a>
    <a href="#features" class="btn-secondary">See Features</a>
  </div>
</div>
<div class="stats-bar">{stats_html}</div>
<section id="features">
  <div class="section-label">Core Capabilities</div>
  <h2 class="section-title">Everything you need.<br>Nothing you don't.</h2>
  <p class="section-sub">Built specifically for {', '.join(contract.target_users[:2]) if contract else 'your workflow'}.</p>
  <div class="features-grid">{features_html}</div>
</section>
<div class="pricing-section" id="pricing">
  <div class="pricing-inner">
    <div class="section-label" style="text-align:center">Pricing</div>
    <h2 class="section-title" style="text-align:center">Simple, transparent pricing</h2>
    <p class="section-sub" style="text-align:center;margin-bottom:48px">{contract.revenue_model if contract else ''}</p>
    <div class="pricing-grid">{pricing_html}</div>
  </div>
</div>
<footer>
  <div class="prometheus-badge">
    <strong>PROMETHEUS</strong> Adversarial Venture Engine ·
    Survived <strong>{len(mission.kill_reports)}</strong> AI attacks ·
    Survival Score <strong>{mission.survival_score:.0f}%</strong> ·
    Mission ID: <strong>{mission_id[:8]}</strong>
  </div>
  <p style="margin-top:20px">© 2025 {company_name}. Generated autonomously by PROMETHEUS.</p>
</footer>
</body>
</html>""")
@app.get("/health")
async def health():
    return {
        "status": "operational",
        "version": "1.0.0",
        "demo_mode": DEMO_MODE,
        "active_missions": len(_missions)
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)