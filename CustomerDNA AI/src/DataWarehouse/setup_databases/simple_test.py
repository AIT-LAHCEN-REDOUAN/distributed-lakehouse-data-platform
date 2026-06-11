"""
CustomerDNA AI - Simple Test
Quick test to verify the dual database system is working
"""

import psycopg2
from config import (
    BASE_DATABASE_NAME, DATA_WAREHOUSE_NAME,
    get_connection_params, USER_CONFIG,
    print_config_summary
)

def test_connection(db_name, user='postgres'):
    """Test connection to a database."""
    try:
        params = get_connection_params(db_name)
        if user == 'superadmin':
            params['user'] = 'superadmin'
            params['password'] = USER_CONFIG['superadmin']['password']
        
        conn = psycopg2.connect(**params)
        cursor = conn.cursor()
        
        # Test simple query
        cursor.execute("SELECT 1")
        result = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"  [OK] Connected to {db_name} as {user}")
        return True
        
    except Exception as e:
        print(f"  [ERROR] Failed to connect to {db_name} as {user}: {str(e)}")
        return False

def check_tables(db_name, schema_name='raw_data'):
    """Check if tables exist in a schema."""
    try:
        conn = psycopg2.connect(**get_connection_params(db_name))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """, (schema_name,))
        
        tables = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        if tables:
            print(f"  [OK] Found {len(tables)} table(s) in {schema_name} schema:")
            for table in tables[:5]:  # Show first 5 tables
                print(f"    • {table}")
            if len(tables) > 5:
                print(f"    ... and {len(tables) - 5} more")
        else:
            print(f"  [INFO] No tables found in {schema_name} schema")
        
        return len(tables) > 0
        
    except Exception as e:
        print(f"  [ERROR] Failed to check tables in {db_name}: {str(e)}")
        return False

def count_records(db_name, schema_name, table_name):
    """Count records in a table."""
    try:
        conn = psycopg2.connect(**get_connection_params(db_name))
        cursor = conn.cursor()
        
        cursor.execute(f'SELECT COUNT(*) FROM {schema_name}.{table_name}')
        count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"  [OK] Table {schema_name}.{table_name} has {count:,} records")
        return count
        
    except Exception as e:
        print(f"  [ERROR] Failed to count records in {schema_name}.{table_name}: {str(e)}")
        return 0

def main():
    """Main function."""
    print("=" * 60)
    print("CUSTOMERDNA AI - SIMPLE TEST")
    print("=" * 60)
    
    print("\n1. Testing PostgreSQL connection...")
    if not test_connection('postgres'):
        print("\n[ERROR] Cannot connect to PostgreSQL. Please check:")
        print("  • Is PostgreSQL running?")
        print("  • Are the credentials in config.py correct?")
        print("  • Can you connect using pgAdmin?")
        return 1
    
    print("\n2. Testing base database...")
    if not test_connection(BASE_DATABASE_NAME):
        print(f"\n[INFO] Base database '{BASE_DATABASE_NAME}' doesn't exist yet.")
        print("  Run 'python setup_databases.py' to create it.")
        base_db_exists = False
    else:
        base_db_exists = True
    
    print("\n3. Testing data warehouse...")
    if not test_connection(DATA_WAREHOUSE_NAME):
        print(f"\n[INFO] Data warehouse '{DATA_WAREHOUSE_NAME}' doesn't exist yet.")
        print("  Run 'python setup_databases.py' to create it.")
        dw_exists = False
    else:
        dw_exists = True
    
    if base_db_exists:
        print("\n4. Checking tables in base database...")
        if check_tables(BASE_DATABASE_NAME, 'raw_data'):
            # Get first table
            try:
                conn = psycopg2.connect(**get_connection_params(BASE_DATABASE_NAME))
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'raw_data' 
                    AND table_type = 'BASE TABLE'
                    LIMIT 1
                """)
                
                result = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if result:
                    table_name = result[0]
                    count_records(BASE_DATABASE_NAME, 'raw_data', table_name)
                    
                    if dw_exists:
                        print(f"\n5. Comparing with data warehouse...")
                        dw_count = count_records(DATA_WAREHOUSE_NAME, 'raw_data', table_name)
                        
                        # Try to get count from base db again for comparison
                        base_count = count_records(BASE_DATABASE_NAME, 'raw_data', table_name)
                        
                        if base_count == dw_count:
                            print(f"\n  [OK] Data is synchronized! Both databases have {base_count:,} records.")
                        else:
                            print(f"\n  [ERROR] Data is not synchronized!")
                            print(f"    Base DB: {base_count:,} records")
                            print(f"    Data Warehouse: {dw_count:,} records")
                            print(f"    Difference: {abs(base_count - dw_count):,} records")
            except Exception as e:
                print(f"  [ERROR] Error checking tables: {str(e)}")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    
    print("\n1. If databases don't exist, run:")
    print("   python setup_databases.py")
    
    print("\n2. To load preprocessed data into base database, run:")
    print("   python load_to_base_db.py")
    
    print("\n3. To synchronize data to data warehouse, run:")
    print("   python sync_databases.py")
    
    print("\n4. To run full system test, run:")
    print("   python test_system.py")
    
    print("\n" + "=" * 60)
    
    return 0

if __name__ == "__main__":
    main()