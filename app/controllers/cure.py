from typing import Dict, List

import app.utils.mongo_utils as mongo_utils
from app.config import settings
from app.helpers.vulnerability_detector import get_openai_client
from openai import OpenAI


async def get_prompts_to_fix_errors(
    user_id: str, github_id: str, repo_id: str
) -> List[Dict]:
    """
    Generate a comprehensive fix prompt for a specific repository.
    """
    report = await mongo_utils.get_vulnerability_report_by_repo_id(
        user_id=user_id,
        github_id=github_id,
        repo_id=repo_id,
    )

    if not report:
        raise ValueError(f"No vulnerability report found for repo_id {repo_id}")

    prompt = build_repo_fix_prompt(report)
    if not prompt:
        return []

    client = get_openai_client()
    plan = await generate_fix_plan(client, prompt)

    return [
        {
            "repo_id": repo_id,
            "repo_name": report.get("repo_name", "unknown-repo"),
            "vulnerability_summary": prompt,
            "llm_fix_plan": plan,
        }
    ]


def build_repo_fix_prompt(report: Dict) -> str:
    repo_name = report.get("repo_name", "unknown-repo")
    total = report.get("total_vulnerabilities", 0)
    severity_counts = {
        "Critical": report.get("critical_count", 0),
        "High": report.get("high_count", 0),
        "Medium": report.get("medium_count", 0),
        "Low": report.get("low_count", 0),
        "Info": report.get("info_count", 0),
    }
    scan_results = report.get("scan_results", [])

    if not total or not scan_results:
        return ""

    prompt_lines = [
        f"Repository: {repo_name}",
        f"Total vulnerabilities: {total}",
        "Severity breakdown:",
    ]
    for severity, count in severity_counts.items():
        prompt_lines.append(f"  - {severity}: {count}")

    prompt_lines.append("")
    prompt_lines.append("Detailed findings:")

    issue_index = 1
    for scan in scan_results:
        file_path = scan.get("file_path", "unknown_file")
        vulnerabilities = scan.get("vulnerabilities", [])

        for vuln in vulnerabilities:
            prompt_lines.extend(
                [
                    f"{issue_index}. File: {file_path}",
                    f"   Type: {vuln.get('vulnerability_type', 'Unknown')}",
                    f"   Severity: {vuln.get('severity', 'Unknown')}",
                    f"   CWE: {vuln.get('cwe_id', 'N/A')} | OWASP: {vuln.get('owasp_category', 'N/A')}",
                    f"   Lines: {vuln.get('start_line', '?')} - {vuln.get('end_line', '?')}",
                    f"   Description: {vuln.get('description', 'No description provided.')}",
                    f"   Code Snippet:\n{vuln.get('code_snippet', '<no code provided>')}",
                    f"   Recommendation: {vuln.get('recommendation', 'No recommendation provided.')}",
                    "",
                ]
            )
            issue_index += 1

    prompt_lines.extend(
        [
            "Please act as a senior application security engineer.",
            "Produce a single fix prompt for Cursor/Trae that covers all vulnerabilities above.",
            "Your output must include:",
            "1. A concise summary of repository risk landscape.",
            "2. Prioritized remediation order explaining why.",
            "3. For each vulnerability, root cause + exact fix instructions referencing files/lines.",
            "4. Secure code snippets or diff-style patches when possible.",
            "5. Tests/validation steps after fixes.",
            "6. Any dependencies/secret rotation steps required.",
        ]
    )

    return "\n".join(prompt_lines)


async def generate_fix_plan(client: OpenAI, prompt: str) -> str:
    loop = None
    try:
        import asyncio

        loop = asyncio.get_event_loop()
    except RuntimeError:
        pass

    def call_openai():
        response = client.responses.create(
            model=settings.OPENAI_MODEL,
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "You are an expert in application security remediation. "
                                "Generate a detailed, actionable fix plan based on the vulnerabilities provided."
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": prompt}],
                },
            ],
        )

        if getattr(response, "output_text", None):
            return response.output_text

        content_parts = []
        for item in getattr(response, "output", []) or []:
            for content in item.get("content", []):
                if "text" in content:
                    content_parts.append(content["text"])
        return "\n".join(content_parts).strip()

    if loop and loop.is_running():
        import functools

        return await loop.run_in_executor(None, call_openai)
    else:
        return call_openai()

