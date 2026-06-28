from __future__ import annotations

from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.expectations import (
    ExpectColumnValuesToBeBetween,
    ExpectColumnValuesToBeInSet,
    ExpectColumnValuesToBeUnique,
    ExpectColumnValuesToMatchRegex,
    ExpectColumnValuesToNotBeNull,
    ExpectTableColumnsToMatchSet,
    ExpectTableRowCountToBeBetween,
    ExpectTableRowCountToEqual,
)
from great_expectations.expectations.metadata_types import FailureSeverity


INTEGER_REGEX = r"^-?\d+$"
INTEGERISH_DECIMAL_REGEX = r"^-?\d+(\.0+)?$"
DECIMAL_REGEX = r"^-?\d+(\.\d+)?$"
DATE_OR_DATETIME_REGEX = r"^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}:\d{2})?$"


def _suite(name: str, expectations: list, notes: list[str]) -> ExpectationSuite:
    suite = ExpectationSuite(
        name=name,
        notes=notes,
        meta={
            "owner": "CustomerDNA AI Team",
            "purpose": "Great Expectations validation suite for Client 1",
        },
    )
    for expectation in expectations:
        suite.add_expectation(expectation)
    return suite


def _columns(columns: list[str]) -> ExpectTableColumnsToMatchSet:
    return ExpectTableColumnsToMatchSet(
        column_set=columns,
        exact_match=True,
        severity=FailureSeverity.CRITICAL,
    )


def _row_count_min(min_value: int = 1, severity: FailureSeverity = FailureSeverity.CRITICAL):
    return ExpectTableRowCountToBeBetween(
        min_value=min_value,
        severity=severity,
    )


def _row_count_equal(value: int):
    return ExpectTableRowCountToEqual(
        value=value,
        severity=FailureSeverity.CRITICAL,
    )


def _not_null(column: str):
    return ExpectColumnValuesToNotBeNull(
        column=column,
        severity=FailureSeverity.CRITICAL,
    )


def _unique(column: str):
    return ExpectColumnValuesToBeUnique(
        column=column,
        severity=FailureSeverity.CRITICAL,
    )


def _in_set(
    column: str,
    value_set: list,
    *,
    severity: FailureSeverity = FailureSeverity.CRITICAL,
    mostly: float = 1.0,
):
    return ExpectColumnValuesToBeInSet(
        column=column,
        value_set=value_set,
        mostly=mostly,
        severity=severity,
    )


def _regex(
    column: str,
    regex: str,
    *,
    severity: FailureSeverity = FailureSeverity.WARNING,
    mostly: float = 0.98,
):
    return ExpectColumnValuesToMatchRegex(
        column=column,
        regex=regex,
        mostly=mostly,
        severity=severity,
    )


def _between(
    column: str,
    *,
    min_value=None,
    max_value=None,
    severity: FailureSeverity = FailureSeverity.WARNING,
    mostly: float = 1.0,
):
    return ExpectColumnValuesToBeBetween(
        column=column,
        min_value=min_value,
        max_value=max_value,
        mostly=mostly,
        severity=severity,
    )


def build_raw_marketing_campaign_suite() -> ExpectationSuite:
    columns = [
        "id",
        "year_birth",
        "education",
        "marital_status",
        "income",
        "kidhome",
        "teenhome",
        "dt_customer",
        "recency",
        "mntwines",
        "mntfruits",
        "mntmeatproducts",
        "mntfishproducts",
        "mntsweetproducts",
        "mntgoldprods",
        "acceptedcmp1",
        "acceptedcmp2",
        "acceptedcmp3",
        "acceptedcmp4",
        "acceptedcmp5",
        "response",
        "numdealspurchases",
        "numwebpurchases",
        "numcatalogpurchases",
        "numstorepurchases",
        "numwebvisitsmonth",
        "complain",
        "z_costcontact",
        "z_revenue",
    ]
    expectations = [
        _columns(columns),
        _row_count_min(),
        _not_null("id"),
        _unique("id"),
        _regex("year_birth", INTEGER_REGEX, mostly=0.995),
        _regex("income", DECIMAL_REGEX, mostly=0.95),
        _regex("dt_customer", DATE_OR_DATETIME_REGEX, mostly=0.995),
        _regex("recency", INTEGER_REGEX, mostly=0.995),
        _in_set("acceptedcmp1", ["0", "1"]),
        _in_set("acceptedcmp2", ["0", "1"]),
        _in_set("acceptedcmp3", ["0", "1"]),
        _in_set("acceptedcmp4", ["0", "1"]),
        _in_set("acceptedcmp5", ["0", "1"]),
        _in_set("response", ["0", "1"]),
        _in_set("complain", ["0", "1"]),
    ]
    notes = [
        "Raw source contract validation for marketing_campaign.",
        "Checks are format-oriented because raw_data is intentionally preserved as TEXT.",
    ]
    return _suite("raw_marketing_campaign_suite", expectations, notes)


def build_raw_ecommerce_customer_churn_suite() -> ExpectationSuite:
    columns = [
        "customerid",
        "churn",
        "tenure",
        "preferredlogindevice",
        "citytier",
        "warehousetohome",
        "preferredpaymentmode",
        "gender",
        "hourspendonapp",
        "numberofdeviceregistered",
        "preferedordercat",
        "satisfactionscore",
        "maritalstatus",
        "numberofaddress",
        "complain",
        "orderamounthikefromlastyear",
        "couponused",
        "ordercount",
        "daysincelastorder",
        "cashbackamount",
    ]
    expectations = [
        _columns(columns),
        _row_count_min(),
        _not_null("customerid"),
        _unique("customerid"),
        _regex("customerid", INTEGER_REGEX, mostly=1.0, severity=FailureSeverity.CRITICAL),
        _in_set("churn", ["0", "1"]),
        _in_set("complain", ["0", "1"]),
        _in_set(
            "satisfactionscore",
            ["1", "2", "3", "4", "5"],
            severity=FailureSeverity.CRITICAL,
        ),
        # These raw values are stored as TEXT and often arrive like "4.0".
        _regex("tenure", INTEGERISH_DECIMAL_REGEX, mostly=0.995),
        _regex("ordercount", INTEGERISH_DECIMAL_REGEX, mostly=0.995),
        _regex("daysincelastorder", INTEGERISH_DECIMAL_REGEX, mostly=0.995),
        _regex("cashbackamount", DECIMAL_REGEX, mostly=0.99),
    ]
    notes = [
        "Raw source contract validation for e_commerce_customer_churn.",
        "Protects key IDs and core label columns before dbt transformations.",
    ]
    return _suite("raw_ecommerce_customer_churn_suite", expectations, notes)


def build_raw_online_retail_suite() -> ExpectationSuite:
    columns = [
        "invoice",
        "stockcode",
        "description",
        "quantity",
        "invoicedate",
        "price",
        "customer_id",
        "country",
    ]
    expectations = [
        _columns(columns),
        _row_count_min(),
        _not_null("invoice"),
        _not_null("stockcode"),
        _not_null("quantity"),
        _not_null("invoicedate"),
        _not_null("price"),
        _regex("quantity", INTEGER_REGEX, mostly=0.995),
        _regex("price", DECIMAL_REGEX, mostly=0.995),
        _regex("invoicedate", DATE_OR_DATETIME_REGEX, mostly=0.995),
    ]
    notes = [
        "Raw source contract validation for online_retail.",
        "Quantity and price remain text in raw_data, so GX validates format rather than typed ranges here.",
    ]
    return _suite("raw_online_retail_suite", expectations, notes)


def build_raw_retailrocket_events_suite() -> ExpectationSuite:
    columns = [
        "timestamp",
        "visitorid",
        "event",
        "itemid",
        "transactionid",
    ]
    expectations = [
        _columns(columns),
        _row_count_min(),
        _not_null("timestamp"),
        _not_null("visitorid"),
        _not_null("event"),
        _not_null("itemid"),
        _regex("timestamp", INTEGER_REGEX, mostly=1.0, severity=FailureSeverity.CRITICAL),
        _regex("visitorid", INTEGER_REGEX, mostly=1.0, severity=FailureSeverity.CRITICAL),
        _regex("itemid", INTEGER_REGEX, mostly=1.0, severity=FailureSeverity.CRITICAL),
        _in_set("event", ["view", "addtocart", "transaction"]),
    ]
    notes = [
        "Raw source contract validation for RetailRocket events.",
        "Focuses on high-trust clickstream fields before staging cleanup.",
    ]
    return _suite("raw_retailrocket_events_suite", expectations, notes)


def build_raw_retailrocket_item_properties_suite() -> ExpectationSuite:
    columns = [
        "timestamp",
        "itemid",
        "property",
        "value",
    ]
    expectations = [
        _columns(columns),
        _row_count_min(),
        _not_null("timestamp"),
        _not_null("itemid"),
        _not_null("property"),
        _not_null("value"),
        _regex("timestamp", INTEGER_REGEX, mostly=1.0, severity=FailureSeverity.CRITICAL),
        _regex("itemid", INTEGER_REGEX, mostly=1.0, severity=FailureSeverity.CRITICAL),
    ]
    notes = [
        "Raw source contract validation for RetailRocket item_properties.",
        "Ensures the product-property history remains structurally stable for downstream item analytics.",
    ]
    return _suite("raw_retailrocket_item_properties_suite", expectations, notes)


def build_raw_retailrocket_category_tree_suite() -> ExpectationSuite:
    columns = [
        "categoryid",
        "parentid",
    ]
    expectations = [
        _columns(columns),
        _row_count_min(),
        _not_null("categoryid"),
        _unique("categoryid"),
        _regex("categoryid", INTEGER_REGEX, mostly=1.0, severity=FailureSeverity.CRITICAL),
    ]
    notes = [
        "Raw source contract validation for RetailRocket category_tree.",
        "Catches category-key drift before product enrichment uses the hierarchy.",
    ]
    return _suite("raw_retailrocket_category_tree_suite", expectations, notes)


def build_analytics_customer_segments_suite() -> ExpectationSuite:
    columns = [
        "customer_id",
        "customer_age",
        "education_level",
        "marital_status",
        "annual_income",
        "kids_at_home",
        "teens_at_home",
        "city_tier",
        "gender",
        "customer_since",
        "customer_tenure_days",
        "customer_tenure_months",
        "days_since_last_purchase",
        "has_churned",
        "churn_risk_score",
        "satisfaction_level",
        "customer_loyalty_tier",
        "customer_activity_level",
        "customer_segment",
        "personality_total_spending",
        "personality_total_purchases",
        "total_campaign_responses",
        "web_visits_last_month",
        "deal_purchase_ratio",
        "web_purchase_ratio",
        "campaign_response_per_spend",
        "total_valid_orders",
        "total_cancelled_orders",
        "gross_sales_amount",
        "net_revenue",
        "avg_order_value",
        "unique_products_purchased",
        "unique_countries_shopped_from",
        "products_per_order",
        "revenue_per_active_day",
        "cancelled_row_ratio",
        "combined_known_spend",
        "effective_spend",
        "effective_order_count",
        "blended_engagement_score",
        "spend_quartile",
        "engagement_quartile",
        "customer_value_tier",
        "engagement_tier",
        "retention_status",
        "primary_purchase_channel",
        "final_customer_segment",
    ]
    expectations = [
        _columns(columns),
        _row_count_min(),
        _not_null("customer_id"),
        _unique("customer_id"),
        _in_set(
            "customer_value_tier",
            ["High Value", "Upper Mid Value", "Mid Value", "Low Value", "Unclassified"],
        ),
        _in_set(
            "engagement_tier",
            ["Highly Engaged", "Engaged", "Moderately Engaged", "Low Engagement", "Unclassified"],
        ),
        _in_set(
            "retention_status",
            ["Churned", "High Risk", "Watchlist", "Stable", "Unknown"],
        ),
        _in_set(
            "primary_purchase_channel",
            ["Web", "Catalog", "Store", "Unknown"],
        ),
        _in_set(
            "final_customer_segment",
            [
                "Lost Customer",
                "VIP Active",
                "High Value Low Engagement",
                "Growth Opportunity",
                "Dormant",
                "Core Customer",
            ],
        ),
        # Negative effective_spend can happen when returns/cancellations dominate.
        # That is a real business outcome, not necessarily a data quality failure.
        _between("effective_order_count", min_value=0),
        _between("blended_engagement_score", min_value=0),
        _between("cancelled_row_ratio", min_value=0, max_value=1),
        _between("churn_risk_score", min_value=0, max_value=3),
    ]
    notes = [
        "Analytics mart validation for customer segments.",
        "This suite protects downstream segmentation, BI, and ML feature consumption.",
    ]
    return _suite("analytics_customer_segments_suite", expectations, notes)


def build_analytics_product_performance_suite() -> ExpectationSuite:
    columns = [
        "item_id",
        "category_id",
        "parent_category_id",
        "category_level",
        "total_events",
        "unique_visitors",
        "unique_transactions",
        "view_count",
        "add_to_cart_count",
        "transaction_count",
        "weighted_event_score",
        "high_engagement_event_count",
        "active_event_days",
        "daily_item_sessions",
        "view_to_cart_rate",
        "view_to_purchase_rate",
        "cart_to_purchase_rate",
        "current_item_price",
        "current_price_tier",
        "property_completeness",
        "brand_name",
        "availability_value",
        "color_value",
        "size_value",
        "latest_property_count",
        "numeric_property_count",
        "important_property_count",
        "has_event_data",
        "has_property_data",
        "has_category_mapping",
        "product_record_source",
        "potential_revenue_signal",
        "activity_quartile",
        "conversion_quartile",
        "product_activity_tier",
        "product_conversion_tier",
        "product_performance_segment",
        "analytics_price_band",
    ]
    expectations = [
        _columns(columns),
        _row_count_min(),
        _not_null("item_id"),
        _unique("item_id"),
        _in_set(
            "product_activity_tier",
            ["High Activity", "Active", "Moderate Activity", "Low Activity", "Unclassified"],
        ),
        _in_set(
            "product_conversion_tier",
            ["High Conversion", "Good Conversion", "Average Conversion", "Low Conversion", "Unclassified"],
        ),
        _in_set(
            "product_performance_segment",
            [
                "Star Product",
                "Cart Interest Low Conversion",
                "High Awareness Low Intent",
                "Low Visibility",
                "Emerging Product",
            ],
        ),
        _in_set(
            "analytics_price_band",
            ["Price Unknown or Free", "Budget", "Affordable", "Mid Market", "Premium"],
        ),
        _between("total_events", min_value=0),
        _between("transaction_count", min_value=0),
        # These ratios are derived from event aggregates and can exceed 1.0
        # when multiple carts or purchases happen per view/cart.
        _between("view_to_cart_rate", min_value=0),
        _between("view_to_purchase_rate", min_value=0),
        _between("cart_to_purchase_rate", min_value=0),
        _in_set(
            "property_completeness",
            ["Complete", "Moderate", "Sparse"],
        ),
        _between("current_item_price", min_value=0),
    ]
    notes = [
        "Analytics mart validation for product performance.",
        "Focuses on rates, tiers, and schema stability for product intelligence use cases.",
    ]
    return _suite("analytics_product_performance_suite", expectations, notes)


def build_analytics_sales_analytics_suite() -> ExpectationSuite:
    columns = [
        "customer_id",
        "customer_age",
        "city_tier",
        "gender",
        "annual_income",
        "customer_loyalty_tier",
        "customer_activity_level",
        "has_churned",
        "total_valid_orders",
        "total_cancelled_orders",
        "total_invoice_rows",
        "active_purchase_days",
        "gross_sales_amount",
        "net_revenue",
        "cancelled_sales_amount",
        "avg_order_value",
        "avg_line_value",
        "avg_unit_price",
        "max_line_value",
        "total_quantity_sold",
        "unique_products_purchased",
        "unique_countries_shopped_from",
        "wholesale_rows",
        "free_item_rows",
        "cancelled_row_ratio",
        "revenue_per_active_day",
        "combined_known_spend",
        "sales_value_band",
        "order_frequency_band",
        "cancellation_risk_band",
        "geography_profile",
    ]
    expectations = [
        _columns(columns),
        _row_count_min(),
        _not_null("customer_id"),
        _unique("customer_id"),
        _in_set(
            "sales_value_band",
            ["No Sales", "Small Account", "Medium Account", "Large Account", "Top Account"],
        ),
        _in_set(
            "order_frequency_band",
            ["Frequent Buyer", "Regular Buyer", "Occasional Buyer", "New Buyer", "No Valid Orders"],
        ),
        _in_set(
            "cancellation_risk_band",
            [
                "High Cancellation Risk",
                "Moderate Cancellation Risk",
                "Low Cancellation Risk",
                "No Cancellation Risk",
            ],
        ),
        _in_set(
            "geography_profile",
            ["Multi-Country Shopper", "Single-Country Shopper", "Unknown Geography"],
        ),
        _between("total_valid_orders", min_value=0),
        _between("gross_sales_amount", min_value=0),
        _between("avg_order_value", min_value=0),
        _between("cancelled_row_ratio", min_value=0, max_value=1),
        _between("unique_countries_shopped_from", min_value=0),
    ]
    notes = [
        "Analytics mart validation for sales analytics.",
        "Serves both BI consumption and future customer-level ML feature use cases.",
    ]
    return _suite("analytics_sales_analytics_suite", expectations, notes)


def build_analytics_business_intelligence_suite() -> ExpectationSuite:
    columns = [
        "generated_at",
        "total_customers",
        "vip_active_customers",
        "churned_customers",
        "high_risk_customers",
        "avg_customer_spend",
        "avg_customer_engagement_score",
        "total_gross_sales",
        "total_net_revenue",
        "total_valid_orders",
        "avg_order_value",
        "avg_cancellation_ratio",
        "total_products",
        "star_products",
        "low_visibility_products",
        "avg_product_conversion_rate",
        "avg_product_events",
        "churn_rate",
        "vip_customer_ratio",
        "star_product_ratio",
    ]
    expectations = [
        _columns(columns),
        _row_count_equal(1),
        _not_null("generated_at"),
        _not_null("total_customers"),
        _not_null("total_products"),
        _between("total_customers", min_value=0),
        _between("total_products", min_value=0),
        _between("total_valid_orders", min_value=0),
        _between("avg_cancellation_ratio", min_value=0, max_value=1),
        _between("churn_rate", min_value=0, max_value=1),
        _between("vip_customer_ratio", min_value=0, max_value=1),
        _between("star_product_ratio", min_value=0, max_value=1),
    ]
    notes = [
        "Single-row executive KPI mart validation.",
        "This suite makes the BI summary table safe for dashboards and presentation outputs.",
    ]
    return _suite("analytics_business_intelligence_suite", expectations, notes)


def build_all_suites() -> dict[str, ExpectationSuite]:
    suites = [
        build_raw_marketing_campaign_suite(),
        build_raw_ecommerce_customer_churn_suite(),
        build_raw_online_retail_suite(),
        build_raw_retailrocket_events_suite(),
        build_raw_retailrocket_item_properties_suite(),
        build_raw_retailrocket_category_tree_suite(),
        build_analytics_customer_segments_suite(),
        build_analytics_product_performance_suite(),
        build_analytics_sales_analytics_suite(),
        build_analytics_business_intelligence_suite(),
    ]
    return {suite.name: suite for suite in suites}
