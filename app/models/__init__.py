"""
ORM models package.

Every model must be imported here, even if unused directly by name,
so that SQLAlchemy's mapper configuration step can resolve the string
based relationships declared with `Mapped["Other"]` (e.g. `Campaign`
referencing `"Template"` and `"History"`). Forgetting to register a
model here is a common source of `InvalidRequestError: expression ...
failed to locate a name` errors at runtime.
"""

from app.models.blacklist import Blacklist
from app.models.campaign import Campaign, CampaignStatus
from app.models.contact import Contact
from app.models.exhibition import Exhibition
from app.models.exhibition_contact import ExhibitionContact
from app.models.history import DeliveryStatus, History
from app.models.lead_stage import LeadStage
from app.models.log import Log
from app.models.setting import Setting
from app.models.template import Template

__all__ = [
    "Blacklist",
    "Campaign",
    "CampaignStatus",
    "Contact",
    "DeliveryStatus",
    "Exhibition",
    "ExhibitionContact",
    "History",
    "LeadStage",
    "Log",
    "Setting",
    "Template",
]
