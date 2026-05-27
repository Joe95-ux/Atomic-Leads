"""Re-export shared models."""

from atomic_models.audit import (
    AuditIssue,
    AuditMetrics,
    AuditRunMeta,
    WebsiteAuditReport,
)
from atomic_models.lead import BusinessLead

# Backward-compatible alias
BusinessLeadInput = BusinessLead

__all__ = [
    "AuditIssue",
    "AuditMetrics",
    "AuditRunMeta",
    "BusinessLead",
    "BusinessLeadInput",
    "WebsiteAuditReport",
]
