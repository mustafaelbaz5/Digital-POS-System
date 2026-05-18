"""
Database Package
"""
from .schema import initialize_database, get_connection
from .dal_budget import (
    get_budget, update_main_budget, set_cash_vault, adjust_cash,
    get_all_platforms, get_platform_by_id,
    add_platform, update_platform_balance, update_wallet_monthly_used,
    deposit_to_platform, reset_wallet_limit_if_needed,
    update_platform_limit, delete_platform, record_daily_commission,
)
from .dal_customers import (
    get_all_groups, add_group, update_group, delete_group,
    get_all_customers, get_customers_by_group, get_customer_by_id,
    add_customer, update_customer, adjust_customer_debt, assign_customer_to_group,
    delete_customer, search_customers, get_export_data,
    get_group_summary,
    get_shipping_codes, get_all_shipping_codes, get_customer_by_shipping_code,
    add_shipping_code, update_shipping_code, delete_shipping_code,
)
from .dal_transactions import (
    add_outbound_transaction, add_inbound_transaction,
    get_transactions, search_by_reference,
    get_customer_statement, mark_as_paid, mark_as_delivered,
    cleanup_paid_transactions, count_finished_transactions, get_dashboard_stats,
    update_transaction_status, delete_transaction, get_unique_service_names,
    cleanup_transactions_before,
    get_platform_day_stats, get_opening_balance, get_closing_balance,
    get_daily_manual_commission, add_manual_commission, get_platform_transactions_for_date,
    get_pending_cash_liability, calculate_wallet_capacity, settle_customer_debt,
)
