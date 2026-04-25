"""
Database Package
"""
from .schema import initialize_database, get_connection
from .dal_budget import (
    get_budget, update_main_budget, set_cash_vault, adjust_cash,
    get_all_platforms, get_platform_by_id,
    add_platform, update_platform_balance, update_wallet_monthly_used,
    deposit_to_platform, reset_wallet_limit_if_needed,
    delete_platform
)
from .dal_customers import (
    get_all_groups, add_group, update_group, delete_group,
    get_all_customers, get_customers_by_group, get_customer_by_id,
    add_customer, update_customer, adjust_customer_debt,
    delete_customer, search_customers
)
from .dal_transactions import (
    add_outbound_transaction, add_inbound_transaction,
    get_transactions, search_by_reference,
    get_customer_statement, mark_as_paid,
    cleanup_paid_transactions, get_dashboard_stats
)
