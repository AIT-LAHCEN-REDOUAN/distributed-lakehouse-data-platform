# CustomerDNA AI - Dual Database System Usage

## Essential Files

1. **config.py** - Database configuration
2. **setup_databases.py** - Create databases and schemas
3. **load_to_base_db.py** - Load CSV data into base database
4. **sync_databases.py** - Synchronize data to data warehouse
5. **simple_test.py** - Quick system verification

## Quick Start

### 1. Update Configuration
Edit `config.py` with your PostgreSQL credentials:
```python
POSTGRES_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'your_password_here',
    'database': 'postgres'
}
```

### 2. Create Databases
```bash
python setup_databases.py
```

### 3. Test Connection
```bash
python simple_test.py
```

### 4. Load Data (when ready)
```bash
python load_to_base_db.py
```

### 5. Synchronize Data
```bash
python sync_databases.py
```

## Database Structure

### Base Database (`CustomerDNA_AI_base_DB`)
- **Schemas**: `raw_data`, `metadata`
- **Purpose**: Raw data storage with automated CSV ingestion
- **Access**: Superadmin only

### Data Warehouse (`CustomerDNA_AI_DW`)
- **Schemas**: `raw_data`, `analytics`, `reports`, `user_tables`
- **Purpose**: Analytical environment with synchronized data
- **Access**: Superadmin only

## User Configuration
- **Single superadmin user** with full access to everything
- **Password**: `superadmin_password_123` (change in config.py)