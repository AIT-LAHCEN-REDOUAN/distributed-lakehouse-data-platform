{% docs project_overview %}

# CustomerDNA AI - Client 1 dbt Project

This dbt project transforms `client1_DW.raw_data` into trusted analytical tables through four layers:

1. **Staging**
   - light cleaning and type standardization
   - one model per raw source
   - preserved source grain

2. **Intermediate**
   - reusable business logic
   - grain-safe joins and aggregations
   - separate customer and product analytical paths

3. **Analytics**
   - final business-facing marts
   - customer, product, sales, and executive KPI outputs

4. **Serving**
   - curated customer-level downstream data products
   - AI/ML-ready feature bases and explainable outputs
   - trusted handoff layer for future segmentation, churn, LTV, persona, and recommendation workflows

The project is intentionally designed to keep raw ingestion, transformation logic, reporting outputs, and AI/ML-oriented serving outputs clearly separated. This makes lineage in `dbt docs` easy to inspect, keeps downstream BI consumers focused on the `analytics` schema, and preserves the `serving` schema as the curated handoff layer for future ML and MLOps-style consumption.

{% enddocs %}

{% docs layer_staging %}

# Staging Layer

The staging layer standardizes raw tables loaded into `raw_data`:

- safe casting from text-based raw tables
- cleaned identifiers and timestamps
- minimal derived flags
- preserved source grain

Staging models should not contain heavy business segmentation or cross-domain joins.

{% enddocs %}

{% docs layer_intermediate %}

# Intermediate Layer

The intermediate layer creates reusable business entities:

- customer profile and customer behavior models
- retail customer summaries
- event and product summaries
- latest known item property rollups

This layer is the main dependency surface for final marts in the analytics layer.

{% enddocs %}

{% docs layer_analytics %}

# Analytics Layer

The analytics layer publishes final marts for reporting and dashboarding:

- `analytics_customer_segments`
- `analytics_product_performance`
- `analytics_sales_analytics`
- `analytics_business_intelligence`

Each analytics model has one stable grain and should be safe for direct BI consumption.

{% enddocs %}

{% docs layer_serving %}

# Serving Layer

The serving layer packages curated customer-level outputs for downstream AI/ML and MLOps-style interpretation:

- `customer_360`
- `segmentation_feature_base`
- `churn_feature_base`
- `ltv_feature_base`
- `persona_base`
- `marketing_recommendation_base`

Serving models should:

- keep one stable downstream grain, usually one row per customer
- expose validated numerical features and explainable business context
- remain traceable back through analytics and intermediate logic
- support future modeling, scoring, persona, and recommendation workflows

Serving models should not replace dashboard marts. Business-facing BI consumption remains centered on the `analytics` schema.

{% enddocs %}
