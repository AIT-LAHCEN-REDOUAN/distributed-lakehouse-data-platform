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





def build_serving_customer_360_suite() -> ExpectationSuite:
    columns = [
        "customer_id",
        "customer_record_source",
        "behavior_record_source",
        "has_personality_data",
        "has_churn_data",
        "has_customer_profile",
        "has_online_retail_summary",
        "birth_year",
        "customer_age",
        "education_level",
        "marital_status",
        "gender",
        "annual_income",
        "household_size",
        "kids_at_home",
        "teens_at_home",
        "city_tier",
        "customer_since",
        "customer_tenure_days",
        "customer_tenure_months",
        "days_since_last_purchase",
        "days_since_last_order",
        "customer_segment",
        "final_customer_segment",
        "customer_value_tier",
        "engagement_tier",
        "retention_status",
        "customer_loyalty_tier",
        "customer_activity_level",
        "satisfaction_level",
        "churn_risk_score",
        "has_churned",
        "has_any_complaint",
        "preferred_login_device",
        "preferred_payment_mode",
        "payment_method_category",
        "preferred_order_category",
        "is_multi_channel_customer",
        "number_of_devices_registered",
        "hours_spent_on_app",
        "personality_segment_hint",
        "total_campaign_responses",
        "deals_purchases",
        "web_purchases",
        "catalog_purchases",
        "store_purchases",
        "web_visits_last_month",
        "deal_purchase_ratio",
        "web_purchase_ratio",
        "campaign_response_per_spend",
        "primary_purchase_channel",
        "campaign_dataset_total_spending",
        "campaign_dataset_total_purchases",
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
        "products_per_order",
        "combined_known_spend",
        "effective_spend",
        "effective_order_count",
        "blended_engagement_score",
        "sales_value_band",
        "order_frequency_band",
        "cancellation_risk_band",
        "geography_profile",
        "customer_360_record_source",
    ]
    expectations = [
        _columns(columns),
        _row_count_min(),
        _not_null("customer_id"),
        _unique("customer_id"),
        _in_set(
            "customer_360_record_source",
            [
                "segments_sales_profile",
                "segments_and_sales",
                "segments_and_profile",
                "sales_and_profile",
                "segments_only",
                "sales_only",
                "profile_only",
                "unknown",
            ],
        ),
        _in_set(
            "customer_value_tier",
            ["High Value", "Upper Mid Value", "Mid Value", "Low Value", "Unclassified"],
            severity=FailureSeverity.WARNING,
        ),
        _in_set(
            "engagement_tier",
            ["Highly Engaged", "Engaged", "Moderately Engaged", "Low Engagement", "Unclassified"],
            severity=FailureSeverity.WARNING,
        ),
        _in_set(
            "retention_status",
            ["Churned", "High Risk", "Watchlist", "Stable", "Unknown"],
            severity=FailureSeverity.WARNING,
        ),
        _in_set(
            "primary_purchase_channel",
            ["Web", "Catalog", "Store", "Unknown"],
            severity=FailureSeverity.WARNING,
        ),
        _between("churn_risk_score", min_value=0, max_value=3),
        _between("cancelled_row_ratio", min_value=0, max_value=1),
        _between("gross_sales_amount", min_value=0),
        _between("avg_order_value", min_value=0),
        _between("total_valid_orders", min_value=0),
    ]
    notes = [
        "Serving-layer validation for customer_360.",
        "Protects the unified customer handoff layer that feeds feature bases, personas, and recommendation outputs.",
    ]
    return _suite("serving_customer_360_suite", expectations, notes)


def build_serving_segmentation_feature_base_suite() -> ExpectationSuite:
    columns = [
        "customer_id",
        "customer_360_record_source",
        "has_personality_data_flag",
        "has_churn_data_flag",
        "has_customer_profile_flag",
        "has_online_retail_summary_flag",
        "gender_category",
        "marital_status_category",
        "education_level_category",
        "city_tier_category",
        "primary_purchase_channel_category",
        "payment_method_category",
        "preferred_login_device",
        "preferred_order_category",
        "feature_customer_age",
        "feature_annual_income",
        "feature_household_size",
        "feature_kids_at_home",
        "feature_teens_at_home",
        "feature_customer_tenure_months",
        "feature_customer_tenure_days",
        "feature_days_since_last_purchase",
        "feature_days_since_last_order",
        "feature_hours_spent_on_app",
        "feature_number_of_devices_registered",
        "feature_web_visits_last_month",
        "feature_total_campaign_responses",
        "feature_deals_purchases",
        "feature_web_purchases",
        "feature_catalog_purchases",
        "feature_store_purchases",
        "feature_campaign_dataset_total_spending",
        "feature_campaign_dataset_total_purchases",
        "feature_total_valid_orders",
        "feature_total_cancelled_orders",
        "feature_active_purchase_days",
        "feature_gross_sales_amount",
        "feature_net_revenue",
        "feature_avg_order_value",
        "feature_total_quantity_sold",
        "feature_unique_products_purchased",
        "feature_unique_countries_shopped_from",
        "feature_cancelled_row_ratio",
        "feature_revenue_per_active_day",
        "feature_combined_known_spend",
        "feature_effective_spend",
        "feature_effective_order_count",
        "feature_blended_engagement_score",
        "feature_churn_risk_score",
        "feature_has_churned_flag",
        "feature_has_any_complaint_flag",
        "feature_is_multi_channel_customer_flag",
        "feature_spend_per_valid_order",
        "feature_quantity_per_valid_order",
        "feature_product_diversity_per_order",
        "feature_order_frequency_per_month",
        "feature_campaign_response_rate",
        "feature_deal_purchase_share",
        "feature_web_purchase_share",
        "feature_catalog_purchase_share",
        "feature_store_purchase_share",
        "feature_revenue_per_product",
        "feature_digital_engagement_index",
        "reference_personality_segment",
        "reference_final_customer_segment",
        "reference_customer_value_tier",
        "reference_engagement_tier",
        "reference_retention_status",
        "reference_sales_value_band",
        "reference_order_frequency_band",
        "reference_cancellation_risk_band",
        "reference_geography_profile",
    ]
    expectations = [
        _columns(columns),
        _row_count_min(),
        _not_null("customer_id"),
        _unique("customer_id"),
        _in_set("has_personality_data_flag", [0, 1]),
        _in_set("has_churn_data_flag", [0, 1]),
        _in_set("has_customer_profile_flag", [0, 1]),
        _in_set("has_online_retail_summary_flag", [0, 1]),
        _in_set("feature_has_churned_flag", [0, 1]),
        _in_set("feature_has_any_complaint_flag", [0, 1]),
        _in_set("feature_is_multi_channel_customer_flag", [0, 1]),
        _in_set(
            "reference_final_customer_segment",
            [
                "Lost Customer",
                "VIP Active",
                "High Value Low Engagement",
                "Growth Opportunity",
                "Dormant",
                "Core Customer",
                "Unknown",
            ],
        ),
        _in_set(
            "reference_customer_value_tier",
            ["High Value", "Upper Mid Value", "Mid Value", "Low Value", "Unclassified"],
        ),
        _in_set(
            "reference_engagement_tier",
            ["Highly Engaged", "Engaged", "Moderately Engaged", "Low Engagement", "Unclassified"],
        ),
        _in_set(
            "reference_retention_status",
            ["Churned", "High Risk", "Watchlist", "Stable", "Unknown"],
        ),
        _between("feature_customer_age", min_value=0),
        _between("feature_customer_tenure_months", min_value=0),
        _between("feature_cancelled_row_ratio", min_value=0, max_value=1),
        _between("feature_churn_risk_score", min_value=0, max_value=3),
        _between("feature_deal_purchase_share", min_value=0, max_value=1),
        _between("feature_web_purchase_share", min_value=0, max_value=1),
        _between("feature_catalog_purchase_share", min_value=0, max_value=1),
        _between("feature_store_purchase_share", min_value=0, max_value=1),
        _between("feature_campaign_response_rate", min_value=0),
    ]
    notes = [
        "Serving-layer validation for segmentation_feature_base.",
        "Protects clustering-ready customer features and their reference segmentation labels.",
    ]
    return _suite("serving_segmentation_feature_base_suite", expectations, notes)


def build_serving_churn_feature_base_suite() -> ExpectationSuite:
    columns = [
        "customer_id",
        "customer_360_record_source",
        "has_personality_data_flag",
        "has_churn_data_flag",
        "has_customer_profile_flag",
        "has_online_retail_summary_flag",
        "gender_category",
        "marital_status_category",
        "education_level_category",
        "city_tier_category",
        "preferred_login_device_category",
        "preferred_payment_mode_category",
        "preferred_order_category",
        "payment_method_category",
        "customer_activity_level_category",
        "customer_loyalty_tier_category",
        "satisfaction_level_category",
        "feature_customer_age",
        "feature_annual_income",
        "feature_household_size",
        "feature_kids_at_home",
        "feature_teens_at_home",
        "feature_customer_tenure_months",
        "feature_customer_tenure_days",
        "feature_days_since_last_purchase",
        "feature_days_since_last_order",
        "feature_hours_spent_on_app",
        "feature_number_of_devices_registered",
        "feature_web_visits_last_month",
        "feature_total_campaign_responses",
        "feature_deals_purchases",
        "feature_web_purchases",
        "feature_catalog_purchases",
        "feature_store_purchases",
        "feature_campaign_dataset_total_spending",
        "feature_campaign_dataset_total_purchases",
        "feature_total_valid_orders",
        "feature_total_cancelled_orders",
        "feature_active_purchase_days",
        "feature_gross_sales_amount",
        "feature_net_revenue",
        "feature_avg_order_value",
        "feature_total_quantity_sold",
        "feature_unique_products_purchased",
        "feature_cancelled_row_ratio",
        "feature_revenue_per_active_day",
        "feature_combined_known_spend",
        "feature_effective_spend",
        "feature_effective_order_count",
        "feature_blended_engagement_score",
        "feature_churn_risk_score",
        "target_has_churned_flag",
        "feature_has_any_complaint_flag",
        "feature_is_multi_channel_customer_flag",
        "feature_order_recency_ratio",
        "feature_purchase_recency_ratio",
        "feature_order_cancellation_share",
        "feature_spend_per_month",
        "feature_orders_per_month",
        "feature_digital_engagement_index",
        "feature_low_satisfaction_flag",
        "reference_churn_risk_band",
        "reference_retention_status",
        "reference_final_customer_segment",
        "reference_customer_value_tier",
    ]
    expectations = [
        _columns(columns),
        _row_count_min(),
        _not_null("customer_id"),
        _unique("customer_id"),
        _in_set("target_has_churned_flag", [0, 1]),
        _in_set("feature_has_any_complaint_flag", [0, 1]),
        _in_set("feature_is_multi_channel_customer_flag", [0, 1]),
        _in_set("feature_low_satisfaction_flag", [0, 1]),
        _in_set("reference_churn_risk_band", ["Critical", "Elevated", "Stable", "Unknown"]),
        _in_set("reference_retention_status", ["Churned", "High Risk", "Watchlist", "Stable", "Unknown"]),
        _between("feature_churn_risk_score", min_value=0, max_value=3),
        _between("feature_cancelled_row_ratio", min_value=0, max_value=1),
        _between("feature_order_recency_ratio", min_value=0),
        _between("feature_purchase_recency_ratio", min_value=0),
        _between("feature_order_cancellation_share", min_value=0, max_value=1),
        _between("feature_orders_per_month", min_value=0),
        _between("feature_spend_per_month", min_value=0),
    ]
    notes = [
        "Serving-layer validation for churn_feature_base.",
        "Protects supervised churn modeling inputs, binary target integrity, and core retention reference labels.",
    ]
    return _suite("serving_churn_feature_base_suite", expectations, notes)


def build_serving_ltv_feature_base_suite() -> ExpectationSuite:
    columns = [
        "customer_id",
        "customer_360_record_source",
        "has_personality_data_flag",
        "has_churn_data_flag",
        "has_customer_profile_flag",
        "has_online_retail_summary_flag",
        "gender_category",
        "marital_status_category",
        "education_level_category",
        "city_tier_category",
        "primary_purchase_channel_category",
        "geography_profile_category",
        "feature_customer_age",
        "feature_annual_income",
        "feature_household_size",
        "feature_customer_tenure_months",
        "feature_customer_tenure_days",
        "feature_days_since_last_purchase",
        "feature_total_campaign_responses",
        "feature_web_visits_last_month",
        "feature_deals_purchases",
        "feature_web_purchases",
        "feature_catalog_purchases",
        "feature_store_purchases",
        "feature_campaign_dataset_total_spending",
        "feature_campaign_dataset_total_purchases",
        "feature_total_valid_orders",
        "feature_active_purchase_days",
        "feature_avg_order_value",
        "feature_total_quantity_sold",
        "feature_unique_products_purchased",
        "feature_unique_countries_shopped_from",
        "feature_revenue_per_active_day",
        "feature_combined_known_spend",
        "feature_effective_spend",
        "feature_effective_order_count",
        "feature_blended_engagement_score",
        "feature_churn_risk_score",
        "feature_is_multi_channel_customer_flag",
        "feature_has_any_complaint_flag",
        "feature_cross_border_flag",
        "feature_channel_mix_count",
        "feature_monetary_per_month",
        "feature_revenue_per_order",
        "feature_quantity_per_order",
        "feature_product_diversity_per_order",
        "feature_campaign_response_rate",
        "feature_revenue_per_product",
        "feature_digital_value_index",
        "target_observed_ltv_proxy",
        "target_observed_net_revenue",
        "target_observed_total_valid_orders",
        "reference_customer_value_tier",
        "reference_sales_value_band",
        "reference_final_customer_segment",
    ]
    expectations = [
        _columns(columns),
        _row_count_min(),
        _not_null("customer_id"),
        _unique("customer_id"),
        _in_set("feature_is_multi_channel_customer_flag", [0, 1]),
        _in_set("feature_has_any_complaint_flag", [0, 1]),
        _in_set("feature_cross_border_flag", [0, 1]),
        _in_set(
            "reference_customer_value_tier",
            ["High Value", "Upper Mid Value", "Mid Value", "Low Value", "Unclassified"],
        ),
        _in_set(
            "reference_sales_value_band",
            ["No Sales", "Small Account", "Medium Account", "Large Account", "Top Account", "Unknown"],
        ),
        _between("feature_channel_mix_count", min_value=0, max_value=3),
        _between("feature_monetary_per_month", min_value=0),
        _between("feature_quantity_per_order", min_value=0),
        _between("feature_product_diversity_per_order", min_value=0),
        _between("feature_campaign_response_rate", min_value=0),
        _between("target_observed_total_valid_orders", min_value=0),
    ]
    notes = [
        "Serving-layer validation for ltv_feature_base.",
        "Protects value-modeling features and observed LTV proxy targets for future regression experimentation.",
        "Negative revenue-like values are allowed here because returns and cancellations can dominate for some customers.",
    ]
    return _suite("serving_ltv_feature_base_suite", expectations, notes)


def build_serving_persona_base_suite() -> ExpectationSuite:
    columns = [
        "customer_id",
        "customer_360_record_source",
        "final_customer_segment",
        "customer_value_tier",
        "engagement_tier",
        "retention_status",
        "primary_purchase_channel",
        "geography_profile",
        "customer_age",
        "annual_income",
        "effective_spend",
        "total_valid_orders",
        "churn_risk_score",
        "web_visits_last_month",
        "hours_spent_on_app",
        "deals_purchases",
        "web_purchases",
        "catalog_purchases",
        "store_purchases",
        "persona_name",
        "digital_affinity",
        "price_sensitivity",
        "lifecycle_stage",
        "channel_preference_profile",
        "primary_marketing_message",
        "persona_summary",
    ]
    expectations = [
        _columns(columns),
        _row_count_min(),
        _not_null("customer_id"),
        _unique("customer_id"),
        _in_set(
            "persona_name",
            [
                "Premium Loyalist",
                "At-Risk High Spender",
                "Growth Challenger",
                "Dormant Customer",
                "Lost Customer",
                "Promo-Driven Regular",
                "Digital Explorer",
                "Core Relationship Customer",
            ],
        ),
        _in_set(
            "digital_affinity",
            ["High Digital Affinity", "Moderate Digital Affinity", "Low Digital Affinity"],
        ),
        _in_set(
            "price_sensitivity",
            ["High Price Sensitivity", "Moderate Price Sensitivity", "Low Price Sensitivity"],
        ),
        _in_set(
            "lifecycle_stage",
            ["Lost", "At Risk", "Dormant", "New", "Established", "Active"],
        ),
        _between("total_valid_orders", min_value=0),
        _between("churn_risk_score", min_value=0, max_value=3),
    ]
    notes = [
        "Serving-layer validation for persona_base.",
        "Protects human-readable persona outputs and lifecycle interpretation consistency.",
        "Persona records may legitimately carry negative effective_spend when returns outweigh purchases.",
    ]
    return _suite("serving_persona_base_suite", expectations, notes)


def build_serving_marketing_recommendation_base_suite() -> ExpectationSuite:
    columns = [
        "customer_id",
        "customer_360_record_source",
        "persona_name",
        "lifecycle_stage",
        "digital_affinity",
        "price_sensitivity",
        "final_customer_segment",
        "customer_value_tier",
        "engagement_tier",
        "retention_status",
        "recommendation_priority_score",
        "recommendation_priority_band",
        "recommended_campaign_objective",
        "recommended_offer_type",
        "recommended_channel",
        "recommended_next_best_action",
        "recommended_contact_timing",
        "recommendation_reason_code",
    ]
    expectations = [
        _columns(columns),
        _row_count_min(),
        _not_null("customer_id"),
        _unique("customer_id"),
        _not_null("recommended_campaign_objective"),
        _not_null("recommended_offer_type"),
        _not_null("recommended_channel"),
        _not_null("recommended_next_best_action"),
        _not_null("recommended_contact_timing"),
        _in_set("recommendation_priority_band", ["Critical", "High", "Medium", "Low"]),
        _in_set(
            "recommended_campaign_objective",
            ["Retention", "Growth", "Loyalty Expansion", "Reactivation", "Nurture"],
        ),
        _in_set(
            "recommended_offer_type",
            [
                "Win-Back Incentive",
                "Premium Upsell",
                "Discount Offer",
                "Digital Cross-Sell",
                "Bundle Recommendation",
                "Personalized Content",
            ],
        ),
        _in_set("recommended_channel", ["Email", "SMS", "Push / Mobile"]),
        _in_set(
            "recommended_contact_timing",
            ["Immediate", "Within 24 Hours", "This Week", "This Month"],
        ),
        _between("recommendation_priority_score", min_value=0),
    ]
    notes = [
        "Serving-layer validation for marketing_recommendation_base.",
        "Protects next-best-action outputs used for future activation, campaign logic, and business interpretation.",
    ]
    return _suite("serving_marketing_recommendation_base_suite", expectations, notes)

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
        build_serving_customer_360_suite(),
        build_serving_segmentation_feature_base_suite(),
        build_serving_churn_feature_base_suite(),
        build_serving_ltv_feature_base_suite(),
        build_serving_persona_base_suite(),
        build_serving_marketing_recommendation_base_suite(),
    ]
    return {suite.name: suite for suite in suites}
