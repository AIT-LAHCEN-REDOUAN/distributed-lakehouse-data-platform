"""
CustomerDNA AI - Verify Global Data Warehouse
Verify data loaded into Global_DW
"""

import sys
import psycopg2
from psycopg2 import sql
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))
from global_config import (
    GLOBAL_DW_CONFIG, get_global_dw_connection_params
)

def verify_global_dw():
    """Verify data in Global_DW."""
    print("=" * 60)
    print("CUSTOMERDNA AI - VERIFY GLOBAL DATA WAREHOUSE")
    print("=" * 60)
    
    try:
        # Connect to Global DW
        conn = psycopg2.connect(**get_global_dw_connection_params())
        cursor = conn.cursor()
        schema = GLOBAL_DW_CONFIG['schema']
        
        print(f"[INFO] Connected to Global_DW: {GLOBAL_DW_CONFIG['database']}")
        print(f"[INFO] Schema: {schema}")
        
        # 1. Check clients table
        print(f"\n[INFO] 1. Checking clients table...")
        cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}.clients").format(
            sql.Identifier(schema)
        ))
        client_count = cursor.fetchone()[0]
        print(f"  [INFO] Total clients: {client_count}")
        
        cursor.execute(sql.SQL("SELECT client_id, client_name, client_code, industry, country FROM {}.clients").format(
            sql.Identifier(schema)
        ))
        clients = cursor.fetchall()
        for client_id, client_name, client_code, industry, country in clients:
            print(f"  • Client {client_id}: {client_name} ({client_code})")
            print(f"    Industry: {industry}, Country: {country}")
        
        # 2. Check global_customers table
        print(f"\n[INFO] 2. Checking global_customers table...")
        cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}.global_customers").format(
            sql.Identifier(schema)
        ))
        customer_count = cursor.fetchone()[0]
        print(f"  [INFO] Total customers: {customer_count}")
        
        cursor.execute(sql.SQL("""
            SELECT client_id, COUNT(*) as customer_count 
            FROM {}.global_customers 
            GROUP BY client_id 
            ORDER BY client_id
        """).format(sql.Identifier(schema)))
        
        customer_stats = cursor.fetchall()
        for client_id, count in customer_stats:
            print(f"  • Client {client_id}: {count:,} customers")
        
        # 3. Check global_transactions table
        print(f"\n[INFO] 3. Checking global_transactions table...")
        cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}.global_transactions").format(
            sql.Identifier(schema)
        ))
        transaction_count = cursor.fetchone()[0]
        print(f"  [INFO] Total transactions: {transaction_count}")
        
        # 4. Check global_interactions table
        print(f"\n[INFO] 4. Checking global_interactions table...")
        cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}.global_interactions").format(
            sql.Identifier(schema)
        ))
        interaction_count = cursor.fetchone()[0]
        print(f"  [INFO] Total interactions: {interaction_count}")
        
        cursor.execute(sql.SQL("""
            SELECT client_id, COUNT(*) as interaction_count 
            FROM {}.global_interactions 
            GROUP BY client_id 
            ORDER BY client_id
        """).format(sql.Identifier(schema)))
        
        interaction_stats = cursor.fetchall()
        for client_id, count in interaction_stats:
            print(f"  • Client {client_id}: {count:,} interactions")
        
        # 5. Check global_rfm_segments table
        print(f"\n[INFO] 5. Checking global_rfm_segments table...")
        cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}.global_rfm_segments").format(
            sql.Identifier(schema)
        ))
        rfm_count = cursor.fetchone()[0]
        print(f"  [INFO] Total RFM segments: {rfm_count}")
        
        # 6. Check global_churn_metrics table
        print(f"\n[INFO] 6. Checking global_churn_metrics table...")
        cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}.global_churn_metrics").format(
            sql.Identifier(schema)
        ))
        churn_count = cursor.fetchone()[0]
        print(f"  [INFO] Total churn metrics: {churn_count}")
        
        # 7. Check data_sync_log table
        print(f"\n[INFO] 7. Checking data_sync_log table...")
        cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}.data_sync_log").format(
            sql.Identifier(schema)
        ))
        log_count = cursor.fetchone()[0]
        print(f"  [INFO] Total sync logs: {log_count}")
        
        cursor.execute(sql.SQL("""
            SELECT sync_type, table_name, records_processed, 
                   records_inserted, status, start_time
            FROM {}.data_sync_log 
            ORDER BY start_time DESC 
            LIMIT 5
        """).format(sql.Identifier(schema)))
        
        logs = cursor.fetchall()
        print(f"  [INFO] Recent sync logs:")
        for sync_type, table_name, processed, inserted, status, start_time in logs:
            print(f"  • {start_time}: {sync_type} for {table_name}")
            print(f"    Processed: {processed:,}, Inserted: {inserted:,}, Status: {status}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"• Clients: {client_count}")
        print(f"• Customers: {customer_count:,}")
        print(f"• Transactions: {transaction_count:,}")
        print(f"• Interactions: {interaction_count:,}")
        print(f"• RFM Segments: {rfm_count:,}")
        print(f"• Churn Metrics: {churn_count:,}")
        print(f"• Sync Logs: {log_count}")
        
        print("\n" + "=" * 60)
        print("VERIFICATION COMPLETED")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = verify_global_dw()
    sys.exit(0 if success else 1)