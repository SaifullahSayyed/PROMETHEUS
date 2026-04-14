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
SYSTEM = """You are an elite penetration tester and security architect with 15 years of offensive security experience. Your job is to find every security vulnerability in this company's product and code. You are adversarial, thorough, and you never miss anything.
You specialize in OWASP Top 10, cloud security misconfigurations, API security, authentication bypasses, and business logic vulnerabilities.
Analyze the provided company blueprint and generated code for ALL of these categories:
1. SQL INJECTION: Raw string concatenation in queries, %-format instead of ? placeholders.
2. AUTHENTICATION FAILURES: Missing JWT validation, tokens without expiry, weak JWT secrets, algorithm confusion.
3. BROKEN ACCESS CONTROL (IDOR): User A fetching user B's data, missing ownership checks.
4. RATE LIMITING: Login/signup/password reset endpoints with no rate limiting.
5. HARDCODED SECRETS: API keys, JWT secrets, database credentials in source code.
6. INPUT VALIDATION: Missing max length enforcement, no content-type validation, no file type checking.
7. CSRF: State-changing endpoints without CSRF tokens, missing SameSite cookie attribute.
8. INFORMATION DISCLOSURE: Stack traces in error handlers, debug endpoints, verbose error messages.
9. SENSITIVE DATA EXPOSURE: Plaintext passwords, PII in logs, payment data in database.
10. SECURITY MISCONFIGURATION: Broad CORS (allow-origin: *), missing HTTPS, missing security headers.
Output ONLY a JSON array of kill report objects. No explanation. No markdown. Raw JSON array starting with [ and ending with ].
Each object must have exactly these fields:
{
  "critic_type": "SECURITY",
  "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
  "title": "string — short, specific title",
  "description": "string — specific to the actual code/spec provided",
  "affected_layer": "CODE" | "SPEC" | "ARCHITECTURE",
  "kill_potential": integer 1-10,
  "suggested_fix": "string — specific fix with code example if applicable",
  "status": "OPEN"
}
Generate between 4 and 7 kill reports. Severity mapping for kill_potential: CRITICAL=8-10, HIGH=5-7, MEDIUM=3-5, LOW=1-3."""
async def run(
    contract: SharedContract,
    generated_files: Dict[str, str],
    mission: Mission,
    emit_fn: Callable
) -> List[KillReport]:
    await emit_fn("log_entry", {
        "agent": "THE BREACH",
        "message": "Initiating penetration test sequence...",
        "level": "CRITICAL"
    })
    contract_summary = f"""Company: {contract.company_name}
Tech Stack: {contract.tech_stack.backend} + {contract.tech_stack.frontend} + {contract.tech_stack.database}
Auth: {contract.tech_stack.auth}
Compliance Requirements: {', '.join(contract.compliance_requirements)}
API Endpoints:
""" + "\n".join([
        f"- {e.method} {e.path} (auth_required={e.auth_required}): {e.description}"
        for e in contract.api_endpoints
    ])
    code_sample = ""
    for fname, content in list(generated_files.items())[:5]:
        code_sample += f"\n\n### FILE: {fname}\n{content[:1200]}"
    prompt = f"""{SYSTEM}
Analyze this company for security vulnerabilities:
{contract_summary}
Generated Code Sample:
{code_sample[:5000]}
Find all security vulnerabilities. Output ONLY the JSON array."""
    try:
        raw = await gemini_generate(prompt=prompt, max_output_tokens=4000, temperature=0.6)
        reports_data = json.loads(_extract_array(raw))
        reports = []
        for rd in reports_data:
            try:
                rd["critic_type"] = "SECURITY"
                rd["status"] = "OPEN"
                report = KillReport(**rd)
                reports.append(report)
                await emit_fn("kill_report", report.model_dump())
                await emit_fn("log_entry", {
                    "agent": "THE BREACH",
                    "message": f"[{report.severity}] {report.title} — Kill Potential: {report.kill_potential}/10",
                    "level": "CRITICAL" if report.severity == "CRITICAL" else "WARNING"
                })
            except Exception:
                continue
        await emit_fn("log_entry", {
            "agent": "THE BREACH",
            "message": f"Security audit complete. {len(reports)} vulnerabilities filed.",
            "level": "WARNING"
        })
        return reports
    except Exception as e:
        await emit_fn("log_entry", {
            "agent": "THE BREACH",
            "message": f"Security audit error: {str(e)}",
            "level": "WARNING"
        })
        return []