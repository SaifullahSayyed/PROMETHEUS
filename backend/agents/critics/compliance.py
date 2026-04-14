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


SYSTEM = """You are a chief compliance officer and regulatory attorney with 15 years of experience ensuring startups meet GDPR, HIPAA, PCI-DSS, CCPA, COPPA, SOC2, and other regulatory requirements. You have shut down products that violated data privacy laws and have advised hundreds of companies on compliance.

Your job is to find every compliance violation, legal liability, and regulatory risk in this company's product and code.

Analyze for ALL of these compliance categories:
1. GDPR (if collecting data from EU users): Missing consent mechanisms, no right-to-deletion flow, storing data without legal basis, missing privacy policy, no data processing records, missing DPA agreements with processors.
2. PCI-DSS (if handling payment card data): Storing raw card numbers, missing PCI-DSS certification disclosure, transmitting card data without proper encryption.
3. HIPAA (if handling health data): Storing PHI without BAA agreements, missing audit logs for PHI access, insufficient encryption for PHI.
4. CCPA (if serving California users): No "Do Not Sell My Data" link, missing privacy policy with CCPA disclosures.
5. COPPA (if serving users under 13): Missing age verification, collecting data from children without parental consent.
6. DATA RETENTION: No data retention policy, storing data indefinitely, no automated deletion.
7. TERMS OF SERVICE: Missing ToS, ToS that create legal liability, missing refund policy.
8. ACCESSIBILITY: Missing WCAG 2.1 compliance (alt tags, keyboard navigation, color contrast).
9. FINANCIAL REGULATIONS: Money transmission licenses if handling funds, lending regulations if extending credit.
10. INTELLECTUAL PROPERTY: Copyright violations, missing license declarations, open-source compliance.

Output ONLY a JSON array. No explanation. No markdown. Raw JSON array starting with [ and ending with ].

Each object must have exactly these fields:
{
  "critic_type": "COMPLIANCE",
  "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
  "title": "string — short, specific title",
  "description": "string — specific to the actual compliance requirement violated",
  "affected_layer": "SPEC" | "CODE" | "ARCHITECTURE",
  "kill_potential": integer 1-10,
  "suggested_fix": "string — specific regulatory fix with citation",
  "status": "OPEN"
}

Generate between 4 and 7 kill reports. Reference specific regulations (e.g., GDPR Article 13, PCI-DSS Requirement 3.4)."""


async def run(
    contract: SharedContract,
    generated_files: Dict[str, str],
    mission: Mission,
    emit_fn: Callable
) -> List[KillReport]:
    """THE REGULATOR — Compliance Critic Agent."""

    await emit_fn("log_entry", {
        "agent": "THE REGULATOR",
        "message": "Scanning for regulatory violations and legal liabilities...",
        "level": "WARNING"
    })

    compliance_str = "\n".join([f"- {c}" for c in contract.compliance_requirements])
    features_str = "\n".join([f"- {f.name}: {f.description}" for f in contract.core_features])
    pricing_str = "\n".join([f"- {p.name}: ${p.price_monthly_usd}/mo — {p.target_segment}" for p in contract.pricing_tiers])

    schema_str = "\n".join([
        f"- {t.name}: " + ", ".join([f"{c.name}({c.sql_type})" for c in t.columns if any(
            kw in c.name.lower() for kw in ['email', 'name', 'phone', 'address', 'password', 'ssn', 'dob', 'card', 'health']
        )])
        for t in contract.database_schema
    ])

    prompt = f"""{SYSTEM}

Analyze this company for compliance and legal issues:

Company: {contract.company_name}
Problem: {contract.problem_statement}
Target Users: {', '.join(contract.target_users)}
Revenue Model: {contract.revenue_model}

Stated Compliance Requirements: {compliance_str if compliance_str else "None specified"}

Core Features (look for PII collection, payments, health data):
{features_str}

Pricing (look for subscription patterns):
{pricing_str}

PII-Related Database Fields:
{schema_str if schema_str else "Not specified"}

Find all compliance violations. Output ONLY the JSON array."""

    try:
        raw = await gemini_generate(prompt=prompt, max_output_tokens=4000, temperature=0.6)
        reports_data = json.loads(_extract_array(raw))
        reports = []
        for rd in reports_data:
            try:
                rd["critic_type"] = "COMPLIANCE"
                rd["status"] = "OPEN"
                report = KillReport(**rd)
                reports.append(report)
                await emit_fn("kill_report", report.model_dump())
                await emit_fn("log_entry", {
                    "agent": "THE REGULATOR",
                    "message": f"[{report.severity}] {report.title}",
                    "level": "CRITICAL" if report.severity == "CRITICAL" else "WARNING"
                })
            except Exception:
                continue

        await emit_fn("log_entry", {
            "agent": "THE REGULATOR",
            "message": f"Compliance audit complete. {len(reports)} violations filed.",
            "level": "WARNING"
        })
        return reports

    except Exception as e:
        await emit_fn("log_entry", {
            "agent": "THE REGULATOR",
            "message": f"Compliance audit error: {str(e)}",
            "level": "WARNING"
        })
        return []
