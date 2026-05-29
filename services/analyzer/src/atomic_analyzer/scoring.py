from atomic_models.audit import AuditIssue

SEVERITY_PENALTY = {
    "critical": 25,
    "warning": 12,
    "info": 5,
}


def compute_score(issues: list[AuditIssue]) -> int:
    score = 100
    for issue in issues:
        score -= SEVERITY_PENALTY.get(issue.severity, 10)
    return max(0, min(100, score))
