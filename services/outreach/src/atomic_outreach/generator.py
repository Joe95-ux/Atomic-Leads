from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from openai import OpenAI
from pydantic import BaseModel

from atomic_models.audit import WebsiteAuditReport
from atomic_models.classify import outreach_skip_reason, pitch_type
from atomic_models.outreach import OutreachDraft
from atomic_outreach.config import OutreachSettings
from atomic_outreach.prompts import (
    FORBIDDEN_PATTERN,
    PITCH_SYSTEM_PROMPTS,
    REWRITE_USER_TEMPLATE,
)

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
        kind = pitch_type(report)

        skip = outreach_skip_reason(report)
        if skip == "chain_franchise":
            return self._skipped(report, skip, to_email, lead)

        if kind == "no_website" and not self.settings.draft_no_website:
            return self._skipped(report, "no_website", to_email, lead)

        if (
            kind == "standard"
            and not report.issues
            and report.score >= self.settings.skip_healthy_score
        ):
            return self._skipped(report, "healthy_site", to_email, lead)

        try:
            payload = self._generate(report, kind)
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

    def _skipped(
        self,
        report: WebsiteAuditReport,
        reason: str,
        to_email: str | None,
        lead,
    ) -> OutreachDraft:
        return OutreachDraft(
            business=report.business,
            website=report.website,
            subject="",
            body="",
            to_email=to_email,
            status="skipped",
            skip_reason=reason,
            audit_score=report.score,
            audit_issues=report.issues,
            lead=lead,
        )

    def draft_many(self, reports: list[WebsiteAuditReport]) -> list[OutreachDraft]:
        drafts: list[OutreachDraft] = []
        for index, report in enumerate(reports, start=1):
            logger.info("[%s/%s] Drafting for %s", index, len(reports), report.business)
            drafts.append(self.draft_for_report(report))
            if index < len(reports):
                time.sleep(self.settings.delay_ms / 1000)
        return drafts

    def _generate(self, report: WebsiteAuditReport, kind: str) -> EmailPayload:
        user_content = self._build_user_prompt(report, kind)
        system_prompt = PITCH_SYSTEM_PROMPTS.get(kind, PITCH_SYSTEM_PROMPTS["standard"])
        payload = self._call_model(user_content, system_prompt)
        combined = f"{payload.subject}\n{payload.body}"
        if match := self._forbidden.search(combined):
            logger.info("Buzzword detected (%s), rewriting once", match.group(0))
            payload = self._rewrite(payload, system_prompt, match.group(0))
        return payload

    def _build_user_prompt(self, report: WebsiteAuditReport, kind: str) -> str:
        lead = report.lead
        city = lead.city if lead else None
        category = lead.category if lead else None
        phone = lead.phone if lead else None
        raw_issues = report.issues or ["No major issues detected"]
        issues = [re.sub(r"\d+ms", "a few seconds", issue) for issue in raw_issues]

        lines = [
            f"Email type: {kind}",
            f"Business name: {report.business}",
            f"Website: {report.website or 'none'}",
            f"City: {city or 'unknown'}",
            f"Category: {category or 'local business'}",
            f"Phone on Google Maps: {phone or 'unknown'}",
        ]
        if lead and lead.email:
            lines.append(f"Contact email found on site: {lead.email}")
        if kind == "standard":
            lines.extend(
                [
                    f"Audit score (lower = more problems): {report.score}/100",
                    "Issues found:",
                    *[f"- {issue}" for issue in issues[:6]],
                ]
            )
            if report.metrics.is_wordpress:
                lines.append("Note: site runs on WordPress — sender can offer maintenance.")
        elif kind == "no_website":
            lines.append("They have no website — pitch a simple starter site.")
        elif kind == "social_only":
            lines.append(f"Their listed link is social/booking only: {report.website}")
        lines.extend(
            [
                "",
                f"Sender name for sign-off: {self.settings.sender_name or 'Best'}",
                f"Sender context: {self.settings.sender_role}",
            ]
        )
        return "\n".join(lines)

    def _call_model(self, user_content: str, system_prompt: str) -> EmailPayload:
        response = self.client.chat.completions.create(
            model=self.settings.model,
            temperature=0.75,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )
        raw = response.choices[0].message.content or "{}"
        return self._parse_payload(raw)

    def _rewrite(self, original: EmailPayload, system_prompt: str, banned: str) -> EmailPayload:
        response = self.client.chat.completions.create(
            model=self.settings.model,
            temperature=0.6,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
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
