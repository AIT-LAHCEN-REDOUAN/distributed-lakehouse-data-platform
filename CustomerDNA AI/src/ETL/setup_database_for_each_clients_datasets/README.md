# Client Database Setup

This directory contains database setup configurations for each client in the CustomerDNA AI system.

## Structure

```
setup_database_for_each_clients_datasets/
├── README.md                    # This file
├── client_template/             # Template for new clients
│   ├── __init__.py
│   ├── config.py               # Client-specific database configuration
│   ├── setup_databases.py      # Database creation and schema setup
│   ├── load_to_base_db.py      # Load preprocessed data to base database
│   ├── sync_databases.py       # Sync data from base to data warehouse
│   ├── simple_test.py          # Test database connections and synchronization
│   └── USAGE.md                # Client-specific usage instructions
├── client_1/                    # Configuration for client 1
│   ├── __init__.py
│   ├── config.py
│   ├── setup_databases.py
│   ├── load_to_base_db.py
│   ├── sync_databases.py
│   ├── simple_test.py
│   └── USAGE.md
└── client_2/                    # Configuration for client 2 (when added)
    └── ...
```

## Purpose

Each client has their own:
1. **Base Database**: For storing raw/preprocessed data
2. **Data Warehouse**: For analytical work, custom ML models, and reporting
3. **Custom Configuration**: Tailored to their specific datasets and requirements

## Workflow

1. **Setup**: Run `setup_databases.py` to create databases and schemas
2. **Load Data**: Run `load_to_base_db.py` to load preprocessed CSV files
3. **Sync**: Run `sync_databases.py` to copy data to the data warehouse
4. **Custom Analysis**: Use the data warehouse for client-specific analytics and ML

## Integration with Global Data Warehouse

Client databases are separate from the global data warehouse (`DataWarehouse/` directory), which serves as a centralized repository for cross-client analytics and reporting.

## Creating a New Client

1. Copy the `client_template/` directory to `client_X/` (where X is the client ID)
2. Update the configuration in `config.py`
3. Customize the setup scripts as needed
4. Run the setup workflow