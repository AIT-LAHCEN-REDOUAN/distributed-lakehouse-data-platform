# CustomerDNA AI - Client 1 Data Models Documentation

## Overview

This dbt project transforms raw client data into analytical models for business intelligence. The project follows a modular architecture with clear separation between staging, intermediate, and analytical models.

## Data Flow

```
Raw Data (raw_data schema)
    ↓
Staging Models (staging schema)
    ↓
Intermediate Models (intermediate schema)
    ↓
Analytical Models (analytics schema)
    ↓
Reports & Dashboards (reports schema)
```

## Model Categories

### 1. Staging Models (`models/staging/`)

**Purpose**: Clean and standardize raw data from the `raw_data` schema.

**Key Models**:
- `stg_marketing_campaign.sql`: Customer personality analysis data
- `stg_ecommerce_customer_churn.sql`: E-commerce customer churn data
- `stg_online_retail.sql`: Online retail transaction data

**Best Practices**:
- Use `materialized='view'` for flexibility
- Preserve raw data integrity
- Add metadata columns (loaded_at, source_table)
- Handle nulls and data type conversions

### 2. Intermediate Models (`models/intermediate/`)

**Purpose**: Apply business logic and create reusable transformations.

**Key Models**:
- `int_customer_metrics.sql`: Combines customer data from multiple sources

**Best Practices**:
- Use `materialized='table'` for performance
- Document business rules
- Create reusable building blocks
- Optimize for query performance

### 3. Analytical Models (`models/analytics/`)

**Purpose**: Create final tables for business intelligence and reporting.

**Key Models**:
- `dim_customer.sql`: Customer dimension table for star schema

**Best Practices**:
- Follow dimensional modeling principles
- Include surrogate keys
- Add slowly changing dimension logic if needed
- Optimize for dashboard queries

## Data Quality Tests

### Test Location: `tests/`

**Purpose**: Ensure data integrity and consistency.

**Key Tests**:
- `test_customer_data_quality.sql`: Comprehensive customer data validation

**Test Types**:
1. **Uniqueness**: Ensure primary keys are unique
2. **Completeness**: Check for required fields
3. **Validity**: Validate data ranges and formats
4. **Consistency**: Ensure logical relationships

## Macros

### Location: `macros/`

**Purpose**: Reusable SQL functions for common transformations.

**Key Macros**:
- `standardize_text.sql`: Text cleaning and standardization
- Additional macros for email validation, currency formatting, etc.

## Configuration

### `dbt_project.yml`

**Key Settings**:
- Profile: `customerdna_client1`
- Model materializations by category
- Schema assignments
- Test configurations
- Project variables

### `profiles.yml`

**Database Connections**:
- Development: `dev` target (staging schema)
- Production: `prod` target (analytics schema)
- Test: `test` target (test schema)

## Running the Project

### Initial Setup
```bash
# Install dbt
pip install dbt-postgres

# Set up profiles
python setup_dbt.py

# Verify installation
dbt --version
dbt debug
```

### Common Commands
```bash
# Run all models
dbt run

# Run specific models
dbt run --models staging.*
dbt run --models intermediate.*
dbt run --models analytics.*

# Test data quality
dbt test

# Generate documentation
dbt docs generate
dbt docs serve
```

### Environment Variables
```bash
# Required for database connection
CUSTOMERDNA_POSTGRES_PASSWORD=your_password

# Optional for production
PROD_POSTGRES_HOST=production_host
PROD_POSTGRES_PORT=5432
PROD_POSTGRES_USER=production_user
PROD_POSTGRES_PASSWORD=production_password
```

## Schema Reference

### `raw_data` Schema
- Contains original client data
- Preserved without modifications
- Tables loaded from ingested CSV files

### `staging` Schema
- Cleaned and standardized data
- Materialized as views
- Ready for business transformations

### `intermediate` Schema
- Business logic transformations
- Materialized as tables
- Reusable building blocks

### `analytics` Schema
- Final analytical tables
- Optimized for reporting
- Star schema dimensions and facts

### `reports` Schema
- Dashboard-ready tables
- Department-specific views
- Aggregated metrics

### `client_specific` Schema
- Client configurations
- Reference data
- Custom business rules

## Best Practices

### 1. Model Design
- Single responsibility principle
- Clear input/output definitions
- Comprehensive documentation

### 2. Performance
- Appropriate materialization strategies
- Index optimization
- Partitioning for large tables

### 3. Testing
- Test early and often
- Comprehensive test coverage
- Meaningful test failures

### 4. Documentation
- Clear model descriptions
- Column-level documentation
- Business context

### 5. Version Control
- Regular commits
- Clear commit messages
- Branch strategy for features

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Verify database credentials
   - Check network connectivity
   - Confirm database exists

2. **Model Failures**
   - Check SQL syntax
   - Verify column names
   - Review data types

3. **Test Failures**
   - Investigate data quality issues
   - Review test logic
   - Check for data changes

### Debugging Commands
```bash
# Show compiled SQL
dbt compile

# Run specific model with debug
dbt run --models model_name --debug

# Check model dependencies
dbt ls --models model_name
```

## Support

For issues or questions:
1. Check the project documentation
2. Review model comments and README files
3. Contact the development team

## Changelog

### Version 1.0.0
- Initial dbt project setup
- Basic staging, intermediate, and analytical models
- Data quality tests
- Documentation framework