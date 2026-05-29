"""Outreach pitch classification from audit reports."""

from atomic_models.audit import WebsiteAuditReport

PitchType = str  # standard | social_only | no_website | booking | none


def issue_codes(report: WebsiteAuditReport) -> set[str]:
    return {issue.code for issue in report.issue_details}


def pitch_type(report: WebsiteAuditReport) -> PitchType:
    codes = issue_codes(report)
    if report.skip_reason in {"chain_franchise", "no_website"} and not codes:
        return report.skip_reason if report.skip_reason == "no_website" else "none"
    if "chain_franchise" in codes or report.skip_reason == "chain_franchise":
        return "none"
    if report.skip_reason == "no_website" or "no_website" in codes:
        return "no_website"
    if "social_only" in codes:
        return "social_only"
    if "third_party_booking" in codes:
        return "booking"
    return "standard"


def outreach_skip_reason(report: WebsiteAuditReport) -> str | None:
    """Return skip reason if this business should not get a cold email draft."""
    kind = pitch_type(report)
    if kind == "none":
        return "chain_franchise"
    if kind == "standard" and not report.issues and report.score >= 92:
        return "healthy_site"
    return None
