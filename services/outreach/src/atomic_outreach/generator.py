from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from openai import OpenAI
from pydantic import BaseModel

from atomic_models.audit import WebsiteAuditReport
from atomic_models.outreach import OutreachDraft
from atomic_outreach.config import OutreachSettings
from atomic_outreach.prompts import FORBIDDEN_PATTERN, REWRITE_USER_TEMPLATE, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class EmailPayload(BaseModel):
    subject: str
    body: str


class EmailGenerator:
    def __init__(self, settings: OutreachSettings) -> None:
        self.settings = settings
        self.client = OpenAI(api_key=settings.api_key)
        self._forbidden = re.compile(FORBIDDEN_PATTERN, re.IGNORECASE)

    def draft_for_report(self, report: WebsiteAuditReport) -> OutreachDraft:
        lead = report.lead
        to_email = lead.email if lead else None

        if report.audit_status == "skipped" and report.skip_reason == "no_website":
            return OutreachDraft(
                business=report.business,
                website=report.website,
                subject="",
                body="",
                to_email=to_email,
                status="skipped",
                skip_reason="no_website",
                audit_score=report.score,
                audit_issues=report.issues,
                lead=lead,
            )

        if (
            not report.issues
            and report.score >= self.settings.skip_healthy_score
        ):
            return OutreachDraft(
                business=report.business,
                website=report.website,
                subject="",
                body="",
                to_email=to_email,
                status="skipped",
                skip_reason="healthy_site",
                audit_score=report.score,
                audit_issues=report.issues,
                lead=lead,
            )

        try:
            payload = self._generate(report)
            return OutreachDraft(
                business=report.business,
                website=report.website,
                subject=payload.subject.strip(),
                body=payload.body.strip(),
                to_email=to_email,
                audit_score=report.score,
                audit_issues=report.issues,
                lead=lead,
                model=self.settings.model,
            )
        except Exception as exc:
            logger.exception("Failed to draft for %s", report.business)
            return OutreachDraft(
                business=report.business,
                website=report.website,
                subject="",
                body="",
                to_email=to_email,
                status="error",
                skip_reason=str(exc)[:200],
                audit_score=report.score,
                audit_issues=report.issues,
                lead=lead,
                model=self.settings.model,
            )

    def draft_many(self, reports: list[WebsiteAuditReport]) -> list[OutreachDraft]:
        drafts: list[OutreachDraft] = []
        for index, report in enumerate(reports, start=1):
            logger.info("[%s/%s] Drafting for %s", index, len(reports), report.business)
            drafts.append(self.draft_for_report(report))
            if index < len(reports):
                time.sleep(self.settings.delay_ms / 1000)
        return drafts

    def _generate(self, report: WebsiteAuditReport) -> EmailPayload:
        user_content = self._build_user_prompt(report)
        payload = self._call_model(user_content)
        combined = f"{payload.subject}\n{payload.body}"
        if match := self._forbidden.search(combined):
            logger.info("Buzzword detected (%s), rewriting once", match.group(0))
            payload = self._rewrite(payload, match.group(0))
        return payload

    def _build_user_prompt(self, report: WebsiteAuditReport) -> str:
        lead = report.lead
        city = lead.city if lead else None
        category = lead.category if lead else None
        raw_issues = report.issues or ["No major issues detected"]
        issues = [re.sub(r"\d+ms", "a few seconds", issue) for issue in raw_issues]

        lines = [
            f"Business name: {report.business}",
            f"Website: {report.website or 'none'}",
            f"City: {city or 'unknown'}",
            f"Category: {category or 'local business'}",
            f"Audit score (lower = more problems): {report.score}/100",
            "Issues found:",
            *[f"- {issue}" for issue in issues[:6]],
            "",
            f"Sender name for sign-off: {self.settings.sender_name or 'Best'}",
            f"Sender context (one line, optional): {self.settings.sender_role}",
        ]
        return "\n".join(lines)

    def _call_model(self, user_content: str) -> EmailPayload:
        response = self.client.chat.completions.create(
            model=self.settings.model,
            temperature=0.75,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )
        raw = response.choices[0].message.content or "{}"
        return self._parse_payload(raw)

    def _rewrite(self, original: EmailPayload, banned: str) -> EmailPayload:
        response = self.client.chat.completions.create(
            model=self.settings.model,
            temperature=0.6,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": REWRITE_USER_TEMPLATE.format(
                        banned=banned,
                        original=original.model_dump_json(),
                    ),
                },
            ],
        )
        raw = response.choices[0].message.content or "{}"
        return self._parse_payload(raw)

    def _parse_payload(self, raw: str) -> EmailPayload:
        data: dict[str, Any] = json.loads(raw)
        return EmailPayload.model_validate(data)
