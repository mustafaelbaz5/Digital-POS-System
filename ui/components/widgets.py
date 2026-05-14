"""
ui/components/widgets.py — backward-compat re-exports
Import from here still works; prefer importing from ui.components directly.
"""
from ui.components.base import BaseDialog, ScreenShell
from ui.components.cards import (
    CardGroup,
    MiniStatCard,
    PlatformCard,
    StatCard,
    StyledButton,
    StyledCard,
    apply_card_shadow,
)
from ui.components.table import DataTable
from ui.components.date_widgets import DateRangeWidget, SingleDateWidget
from ui.components.misc import (
    SectionTitle,
    GroupLabel,
    InfoRow,
    make_divider,
    make_section_header,
    Toast,
    show_toast,
    make_txn_actions,
)
