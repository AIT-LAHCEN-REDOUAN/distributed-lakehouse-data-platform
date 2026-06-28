# Great Expectations for Client 1

This folder adds a Great Expectations data quality layer on top of the
existing Client 1 ELT stack.

Scope:
- `raw_data` source contract validation
- `analytics` mart validation
- ML-readiness validation for downstream customer analytics tables

The setup is intentionally complementary to dbt:
- dbt owns transformations, lineage, and warehouse-native tests
- Great Expectations owns richer data quality gates and validation reports

Design choices:
- `raw_data` tables are preserved as `TEXT`, so raw GX suites focus on schema,
  required fields, allowed values, and regex-based format checks.
- `analytics` GX suites focus on curated mart quality, numeric ranges, ratios,
  categorical domains, and downstream AI/ML readiness.
- Staging and intermediate logic remains primarily covered by dbt tests.

Files:
- `gx_config.py`: project paths, datasource config, asset registry, checkpoint names
- `gx_suite_definitions.py`: curated expectation suites for raw and analytics layers
- `bootstrap_gx.py`: idempotent setup for GX context, datasource, assets, suites,
  validation definitions, and checkpoints
- `run_gx_validations.py`: convenience runner for raw, analytics, ML, or all checkpoints

Recommended usage:
1. Run `bootstrap_gx.py` once to scaffold the GX file context and register
   project objects.
2. Run `run_gx_validations.py --checkpoint raw` after raw data loads.
3. Run `run_gx_validations.py --checkpoint analytics` after `dbt run`.
4. Run `run_gx_validations.py --checkpoint ml` before any feature extraction,
   training, or model refresh.
