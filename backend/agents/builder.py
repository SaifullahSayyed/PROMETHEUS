import asyncio
import json
import re
from typing import Dict, Callable, Any
from llm import gemini_generate
from models.contract import SharedContract
from models.mission import Mission
def _extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    return text
BLUEPRINT_SYSTEM = """You are a world-class CTO and business architect with 20 years of experience building startups from zero to unicorn. You have worked at Google, Stripe, Airbnb, and advised 200+ startups. Your job is to take a raw business idea and instantly produce a precise, fully-specified company blueprint.
You must output ONLY raw valid JSON matching the SharedContract schema — absolutely no markdown, no explanation, no code fences, no preamble. Only a single JSON object starting with { and ending with }.
The JSON must contain these exact top-level fields:
- company_name: A creative, memorable brand name. NOT generic. Think Stripe, Notion, Figma, Vercel, Linear.
- tagline: A single sentence that explains the product. Max 12 words. Punchy and specific.
- problem_statement: 2-3 sentences explaining exactly what pain exists today and why current solutions fail.
- target_users: Array of 2-4 specific user personas (e.g., "Freelance graphic designers with 3-20 clients", NOT "small businesses")
- core_features: Array of 5-8 Feature objects. Each feature must have: id (feat_001 format), name, description, priority (P0/P1/P2), user_story (format: "As a [persona], I want to [action] so that [benefit]")
- user_journeys: Array of 2-3 UserJourney objects. Each has: persona, steps (array of 4-8 specific action steps), success_condition
- tech_stack: TechStack object with fields: frontend, backend, database, auth, hosting. Choose based on the problem. Be specific.
- database_schema: Array of 3-6 Table objects. Each table has: name, columns (array of Column objects with: name, sql_type using real SQL types like UUID, VARCHAR(255), DECIMAL(10,2), TIMESTAMPTZ, JSONB, BOOLEAN, INTEGER, TEXT), nullable, primary_key, foreign_key, index. relationships (array of strings describing FK relationships).
- api_endpoints: Array of minimum 6 Endpoint objects. Each endpoint has: method (GET/POST/PUT/PATCH/DELETE), path, description, auth_required (boolean), request_schema (object or null), response_schema (object or null).
- pricing_tiers: Array of 2-4 PricingTier objects. Each has: name, price_monthly_usd (real number), price_annual_usd (80% of monthly*12), features (array of 4-6 specific feature strings), target_segment.
- revenue_model: A specific string explaining how money flows.
- go_to_market: A specific channel strategy with real channels.
- compliance_requirements: Array of real compliance items (GDPR, PCI-DSS, HIPAA, CCPA, etc.).
- known_risks: Array of 3-5 specific business/technical risks unique to this domain.
- amendments: Empty array []
- version: 1
Output ONLY the JSON. Nothing else. No explanation. No markdown. Raw JSON starting with { and ending with }."""
async def generate_contract(prompt: str, mission: Mission, emit_fn: Callable) -> SharedContract:
    user_message = f"""Problem statement: {prompt}
Generate the complete SharedContract JSON for this business. Remember:
- Choose a tech stack that actually makes sense for this specific problem domain
- Write real SQL column types (UUID, VARCHAR(255), DECIMAL(10,2), TIMESTAMPTZ, JSONB)
- Generate minimum 6 API endpoints with real RESTful paths
- Give real specific pricing — research the market segment
- Identify ALL compliance requirements
- Name at least 3 real business risks specific to this exact domain
- Use a company_name that sounds like a funded startup
Output ONLY the raw JSON object. No markdown. No explanation."""
    await emit_fn("log_entry", {
        "agent": "BUILDER",
        "message": "Calling Gemini 2.0 Flash to generate company blueprint...",
        "level": "INFO"
    })
    raw = await gemini_generate(
        prompt=user_message,
        system_prompt=BLUEPRINT_SYSTEM,
        max_output_tokens=8192,
        temperature=0.7,
    )
    raw = _extract_json(raw)
    await emit_fn("log_entry", {
        "agent": "BUILDER",
        "message": "Blueprint JSON received. Parsing...",
        "level": "INFO"
    })
    try:
        data = json.loads(raw)
        contract = SharedContract(**data)
        await emit_fn("log_entry", {
            "agent": "BUILDER",
            "message": f"Contract parsed: {contract.company_name} — {contract.tagline}",
            "level": "SUCCESS"
        })
        return contract
    except Exception as e:
        await emit_fn("log_entry", {
            "agent": "BUILDER",
            "message": f"Parse failed: {e}. Retrying...",
            "level": "WARNING"
        })
        retry_message = f"""Problem statement: {prompt}
PREVIOUS ATTEMPT FAILED WITH ERROR: {str(e)}
The previous JSON had a parsing error. Fix it and output ONLY valid JSON matching the SharedContract schema.
No markdown. No explanation. Raw JSON only starting with {  and ending with } ."""
        raw2 = await gemini_generate(
            prompt=retry_message,
            system_prompt=BLUEPRINT_SYSTEM,
            max_output_tokens=8192,
            temperature=0.3,
        )
        raw2 = _extract_json(raw2)
        data2 = json.loads(raw2)
        contract2 = SharedContract(**data2)
        await emit_fn("log_entry", {
            "agent": "BUILDER",
            "message": f"Retry successful: {contract2.company_name}",
            "level": "SUCCESS"
        })
        return contract2
async def construct_codebase(contract: SharedContract, mission: Mission, emit_fn: Callable) -> Dict[str, str]:
    async def generate_frontend(contract: SharedContract) -> Dict[str, str]:
        await emit_fn("log_entry", {
            "agent": "BUILDER",
            "message": "Sub-agent FRONTEND: generating Next.js application...",
            "level": "INFO"
        })
        system = "You are a senior frontend engineer. Generate a complete, production-quality Next.js 14 TypeScript application based on this company blueprint. Every page must have real UI with real components. Use Tailwind CSS. Output each file as a JSON object: {filename: content}. Output ONLY the JSON object, nothing else. No markdown, no explanation."
        features_str = "\n".join([f"- {f.name}: {f.description}" for f in contract.core_features])
        endpoints_str = "\n".join([f"- {e.method} {e.path}: {e.description}" for e in contract.api_endpoints])
        pricing_str = "\n".join([f"- {p.name}: ${p.price_monthly_usd}/mo" for p in contract.pricing_tiers])
        prompt = f"""{system}
Company: {contract.company_name}
Tagline: {contract.tagline}
Tech Stack Frontend: {contract.tech_stack.frontend}
Features:
{features_str}
API Endpoints:
{endpoints_str}
Pricing:
{pricing_str}
Generate a complete Next.js 14 TypeScript app with:
1. app/page.tsx — Landing page with hero section, features grid, pricing table, CTA buttons
2. app/dashboard/page.tsx — Main application dashboard
3. app/layout.tsx — Root layout with metadata, fonts
4. app/globals.css — Complete CSS with modern SaaS styling
5. components/Navbar.tsx — Navigation with logo, links, auth buttons
6. lib/api.ts — Complete typed API client
7. package.json — All dependencies
8. next.config.js — Next.js config
Output ONLY a single JSON object mapping filename to file content."""
        try:
            raw = await gemini_generate(prompt=prompt, max_output_tokens=8000, temperature=0.5)
            return json.loads(_extract_json(raw))
        except Exception:
            return {"frontend/README.md": f"# {contract.company_name} Frontend\n\nGenerated Next.js application for {contract.company_name}."}
    async def generate_backend(contract: SharedContract) -> Dict[str, str]:
        await emit_fn("log_entry", {
            "agent": "BUILDER",
            "message": "Sub-agent BACKEND: generating FastAPI application...",
            "level": "INFO"
        })
        endpoints_str = "\n".join([
            f"- {e.method} {e.path}: {e.description} (auth: {e.auth_required})"
            for e in contract.api_endpoints
        ])
        tables_str = "\n".join([
            f"- {t.name}: " + ", ".join([f"{c.name} {c.sql_type}" for c in t.columns[:5]])
            for t in contract.database_schema
        ])
        prompt = f"""You are a senior backend engineer. Generate a complete FastAPI Python application. Output ONLY a JSON object: { filename: content} . No markdown.
Company: {contract.company_name}
Backend Tech: {contract.tech_stack.backend}
Database: {contract.tech_stack.database}
API Endpoints:
{endpoints_str}
Database Tables:
{tables_str}
Generate:
1. backend/main.py — FastAPI app with all endpoints fully implemented
2. backend/models.py — SQLAlchemy ORM models
3. backend/database.py — Database setup
4. backend/schemas.py — Pydantic schemas
5. backend/auth.py — JWT authentication
6. backend/requirements.txt — All pip dependencies
Output ONLY a single JSON object mapping filename to file content."""
        try:
            raw = await gemini_generate(prompt=prompt, max_output_tokens=8000, temperature=0.5)
            return json.loads(_extract_json(raw))
        except Exception:
            return {"backend/README.md": f"# {contract.company_name} Backend\n\nGenerated FastAPI application."}
    async def generate_database(contract: SharedContract) -> Dict[str, str]:
        await emit_fn("log_entry", {
            "agent": "BUILDER",
            "message": "Sub-agent DATABASE: generating SQL migrations...",
            "level": "INFO"
        })
        tables_str = "\n".join([
            f"Table: {t.name}\nColumns: " + "\n  ".join([
                f"{c.name} {c.sql_type} {'PRIMARY KEY' if c.primary_key else ''} {'NOT NULL' if not c.nullable else ''}"
                for c in t.columns
            ])
            for t in contract.database_schema
        ])
        prompt = f"""You are a senior database engineer. Generate complete SQL migration files for SQLite. Output ONLY a JSON object: { filename: content} . No markdown.
Database Schema for {contract.company_name}:
{tables_str}
Generate:
1. migrations/001_create_tables.sql — CREATE TABLE statements with constraints and indexes
2. migrations/002_seed_data.sql — INSERT statements with 10-15 rows of realistic seed data
Output ONLY a single JSON object mapping filename to file content."""
        try:
            raw = await gemini_generate(prompt=prompt, max_output_tokens=4000, temperature=0.3)
            return json.loads(_extract_json(raw))
        except Exception:
            return {
                "migrations/001_create_tables.sql": f"-- {contract.company_name} Database Schema\n",
                "migrations/002_seed_data.sql": f"-- {contract.company_name} Seed Data\n"
            }
    async def generate_docs(contract: SharedContract) -> Dict[str, str]:
        await emit_fn("log_entry", {
            "agent": "BUILDER",
            "message": "Sub-agent DOCS: generating documentation...",
            "level": "INFO"
        })
        endpoints_str = "\n".join([
            f"### {e.method} {e.path}\n{e.description}\n- Auth required: {e.auth_required}"
            for e in contract.api_endpoints
        ])
        pricing_str = "\n".join([
            f"- **{p.name}**: ${p.price_monthly_usd}/mo — {p.target_segment}"
            for p in contract.pricing_tiers
        ])
        prompt = f"""You are a senior technical writer. Generate complete documentation files. Output ONLY a JSON object: { filename: content} . No markdown fences.
Company: {contract.company_name}
Tagline: {contract.tagline}
Problem: {contract.problem_statement}
Tech Stack: Frontend={contract.tech_stack.frontend}, Backend={contract.tech_stack.backend}
Revenue: {contract.revenue_model}
API Endpoints:
{endpoints_str}
Pricing:
{pricing_str}
Generate:
1. README.md — Setup instructions, what it does, how to run
2. COMPANY_BRIEF.md — Professional one-page company overview
3. API_REFERENCE.md — Full API documentation
Output ONLY a single JSON object mapping filename to file content."""
        try:
            raw = await gemini_generate(prompt=prompt, max_output_tokens=4000, temperature=0.5)
            return json.loads(_extract_json(raw))
        except Exception:
            return {
                "README.md": f"# {contract.company_name}\n\n{contract.tagline}\n\n{contract.problem_statement}",
                "COMPANY_BRIEF.md": f"# {contract.company_name} — Company Brief\n\n{contract.tagline}",
                "API_REFERENCE.md": f"# {contract.company_name} API Reference\n\n"
            }
    await emit_fn("log_entry", {
        "agent": "BUILDER",
        "message": "Launching build agents sequentially: Frontend → Backend → Database → Docs",
        "level": "INFO"
    })
    results = []
    for coro, name in [
        (generate_frontend(contract), "FRONTEND"),
        (generate_backend(contract), "BACKEND"),
        (generate_database(contract), "DATABASE"),
        (generate_docs(contract), "DOCS"),
    ]:
        try:
            result = await coro
            results.append(result)
        except Exception as e:
            results.append(e)
    merged: Dict[str, str] = {}
    agent_names = ["FRONTEND", "BACKEND", "DATABASE", "DOCS"]
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            await emit_fn("log_entry", {
                "agent": "BUILDER",
                "message": f"Sub-agent {agent_names[i]} error: {str(result)}",
                "level": "WARNING"
            })
        elif isinstance(result, dict):
            merged.update(result)
            await emit_fn("log_entry", {
                "agent": "BUILDER",
                "message": f"Sub-agent {agent_names[i]} complete: {len(result)} files generated",
                "level": "SUCCESS"
            })
    return merged