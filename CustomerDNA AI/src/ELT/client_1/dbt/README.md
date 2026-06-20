# CustomerDNA AI - Client 1 dbt Project

This dbt project transforms raw client data into analytical models for business intelligence.

## Project Structure

```
dbt/
├── models/                    # SQL models
│   ├── staging/              # Staging models (raw → clean)
│   ├── intermediate/         # Intermediate transformations
│   ├── analytics/            # Final analytical models
│   └── marts/                # Business marts
├── macros/                   # Reusable SQL macros
├── tests/                    # Data quality tests
├── snapshots/               # Slowly changing dimensions
├── seeds/                   # Static data files
├── analysis/                # Ad-hoc analysis queries
├── dbt_project.yml          # Project configuration
└── profiles.yml             # Database connection profiles
```

## Data Flow

1. **Raw Data**: `client1_DW.raw_data` schema
2. **Staging Models**: Clean and standardize raw data
3. **Intermediate Models**: Business logic transformations
4. **Analytical Models**: Final tables for reporting
5. **Business Marts**: Department-specific views

## Schemas

- **raw_data**: Original client data (preserved)
- **staging**: Cleaned and standardized data
- **intermediate**: Business logic transformations
- **analytics**: Final analytical tables
- **reports**: Dashboard-ready tables
- **client_specific**: Client configurations

## Running dbt

```bash
# Initialize dbt
dbt init

# Run all models
dbt run

# Run specific models
dbt run --models staging.*

# Test data quality
dbt test

# Generate documentation
dbt docs generate
dbt docs serve
```

## Database Connection

- **Host**: localhost:5440
- **Database**: client1_DW
- **Schemas**: raw_data, staging, intermediate, analytics