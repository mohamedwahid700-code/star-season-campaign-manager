"""Modal dialogs: transient windows for creating/editing a single
record or running a multi-step workflow (import, column mapping,
Outlook test send), as opposed to the persistent chrome in
`app.ui.components`.
"""

from app.ui.dialogs.campaign_dialog import CampaignDialog
from app.ui.dialogs.column_mapping_dialog import ColumnMappingDialog
from app.ui.dialogs.contact_dialog import ContactDialog
from app.ui.dialogs.contact_import_dialog import ContactImportDialog
from app.ui.dialogs.contact_picker_dialog import ContactPickerDialog
from app.ui.dialogs.outlook_send_test_dialog import OutlookSendTestDialog
from app.ui.dialogs.template_dialog import TemplateDialog

__all__ = [
    "CampaignDialog",
    "ColumnMappingDialog",
    "ContactDialog",
    "ContactImportDialog",
    "ContactPickerDialog",
    "OutlookSendTestDialog",
    "TemplateDialog",
]
