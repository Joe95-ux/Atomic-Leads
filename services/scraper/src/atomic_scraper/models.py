"""Re-export shared models — use atomic_models directly in new code."""

from atomic_models.lead import BusinessLead, ScrapeRunMeta

__all__ = ["BusinessLead", "ScrapeRunMeta"]
