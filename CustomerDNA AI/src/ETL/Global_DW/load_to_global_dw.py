"""
CustomerDNA AI - Load Data to Global Data Warehouse
Extracts data from client data warehouses and loads into Global_DW
"""

import sys
import psycopg2
from psycopg2 import sql
import os
from datetime import datetime, date
import pandas as pd
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))
from global_config import (
    GLOBAL_DW_CONFIG, get_global_dw_connection_params,
    get_client_dw_connection_params, get_client_dw_db_name
)

class GlobalDWLoader:
    """Loads data from client DWs to Global_DW."""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.global_conn = None
        self.client_conn = None
        self.client_id = None
        self.sync_date = date.today()
    
    def log(self, message, level="INFO"):
        """Log message with simple formatting."""
        if self.verbose:
            if level == "ERROR":
                print(f"[ERROR] {message}")
            elif level == "SUCCESS":
                print(f"[SUCCESS] {message}")
            else:
                print(f"[INFO] {message}")
    
    def connect_to_global_dw(self):
        """Connect to the global data warehouse."""
        try:
            self.global_conn = psycopg2.connect(**get_global_dw_connection_params())
            self.global_conn.autocommit = True
            self.log(f"Connected to global data warehouse: {GLOBAL_DW_CONFIG['database']}")
            
            return True
            
        except Exception as e:
            self.log(f"Failed to connect to global DW: {str(e)}", "ERROR")
            return False
    
    def connect_to_client_dw(self, client_id):
        """Connect to a client data warehouse."""
        try:
            self.client_id = client_id
            client_db_name = get_client_dw_db_name(client_id)
            
            self.client_conn = psycopg2.connect(**get_client_dw_connection_params(client_db_name))
            self.client_conn.autocommit = True
            self.log(f"Connected to client data warehouse: {client_db_name}")
            
            return True
            
        except Exception as e:
            self.log(f"Failed to connect to client DW {client_id}: {str(e)}", "ERROR")
            return False
    
    def get_or_create_client(self, client_name, client_code, industry=None, country=None):
        """Get or create a client record in the clients table."""
        try:
            cursor = self.global_conn.cursor()
            schema = GLOBAL_DW_CONFIG['schema']
            
            # Check if client already exists
            cursor.execute(sql.SQL("""
                SELECT client_id FROM {}.clients 
                WHERE client_code = %s
            """).format(sql.Identifier(schema)), (client_code,))
            
            result = cursor.fetchone()
            
            if result:
                client_id = result[0]
                self.log(f"Client {client_code} already exists with ID: {client_id}")
                
                # Update client information
                cursor.execute(sql.SQL("""
                    UPDATE {}.clients 
                    SET client_name = %s, industry = %s, country = %s, 
                        updated_at = CURRENT_TIMESTAMP
                    WHERE client_id = %s
                """).format(sql.Identifier(schema)), 
                (client_name, industry, country, client_id))
                
            else:
                # Create new client
                cursor.execute(sql.SQL("""
                    INSERT INTO {}.clients 
                    (client_name, client_code, industry, country, onboard_date)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING client_id
                """).format(sql.Identifier(schema)), 
                (client_name, client_code, industry, country, self.sync_date))
                
                client_id = cursor.fetchone()[0]
                self.log(f"Created new client {client_code} with ID: {client_id}")
            
            cursor.close()
            return client_id
            
        except Exception as e:
            self.log(f"Failed to get/create client: {str(e)}", "ERROR")
            return None
    
    def load_customer_personality_data(self):
        """Load customer personality data from client DW to Global_DW."""
        try:
            cursor = self.client_conn.cursor()
            global_cursor = self.global_conn.cursor()
            schema = GLOBAL_DW_CONFIG['schema']
            
            # Find customer personality tables in client DW
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'analytics' 
                AND table_name LIKE '%customer_personality%'
                ORDER BY table_name
            """)
            
            tables = cursor.fetchall()
            
            if not tables:
                self.log("No customer personality tables found in client DW")
                return 0
            
            total_loaded = 0
            
            for table_row in tables:
                table_name = table_row[0]
                self.log(f"Processing customer personality table: {table_name}")
                
                # Get data from client DW
                cursor.execute(sql.SQL("SELECT * FROM analytics.{}").format(
                    sql.Identifier(table_name)
                ))
                
                rows = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description]
                
                if not rows:
                    self.log(f"Table {table_name} is empty")
                    continue
                
                # Map client data to global schema
                loaded_count = 0
                for row in rows:
                    row_dict = dict(zip(column_names, row))
                    
                    try:
                        # Extract relevant fields (adjust based on actual column names)
                        age = row_dict.get('age') or (2024 - row_dict.get('year_birth', 2024))
                        income = row_dict.get('income')
                        education = row_dict.get('education')
                        marital_status = row_dict.get('marital_status')
                        total_spending = row_dict.get('total_spending') or sum([
                            row_dict.get('mntwines', 0),
                            row_dict.get('mntfruits', 0),
                            row_dict.get('mntmeatproducts', 0),
                            row_dict.get('mntfishproducts', 0),
                            row_dict.get('mntsweetproducts', 0),
                            row_dict.get('mntgoldprods', 0)
                        ])
                        
                        # Insert into global_customers table
                        global_cursor.execute(sql.SQL("""
                            INSERT INTO {}.global_customers 
                            (client_id, source_customer_id, age, income, education, 
                             marital_status, total_spending, data_source, sync_date)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (client_id, source_customer_id) 
                            DO UPDATE SET
                                age = EXCLUDED.age,
                                income = EXCLUDED.income,
                                education = EXCLUDED.education,
                                marital_status = EXCLUDED.marital_status,
                                total_spending = EXCLUDED.total_spending,
                                updated_at = CURRENT_TIMESTAMP
                        """).format(sql.Identifier(schema)), 
                        (
                            self.client_id,
                            str(row_dict.get('id', '')),
                            age,
                            income,
                            education,
                            marital_status,
                            total_spending,
                            f"customer_personality_{table_name}",
                            self.sync_date
                        ))
                        
                        loaded_count += 1
                        
                    except Exception as e:
                        self.log(f"Failed to process row: {str(e)}", "ERROR")
                        continue
                
                self.log(f"Loaded {loaded_count} customers from {table_name}")
                total_loaded += loaded_count
            
            cursor.close()
            global_cursor.close()
            
            return total_loaded
            
        except Exception as e:
            self.log(f"Failed to load customer personality data: {str(e)}", "ERROR")
            return 0
    
    def load_rfm_data(self):
        """Load RFM segmentation data from client DW to Global_DW."""
        try:
            cursor = self.client_conn.cursor()
            global_cursor = self.global_conn.cursor()
            schema = GLOBAL_DW_CONFIG['schema']
            
            # Find RFM tables in client DW
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'analytics' 
                AND table_name LIKE '%rfm%'
                ORDER BY table_name
            """)
            
            tables = cursor.fetchall()
            
            if not tables:
                self.log("No RFM tables found in client DW")
                return 0
            
            total_loaded = 0
            
            for table_row in tables:
                table_name = table_row[0]
                self.log(f"Processing RFM table: {table_name}")
                
                # Get data from client DW
                cursor.execute(sql.SQL("SELECT * FROM analytics.{}").format(
                    sql.Identifier(table_name)
                ))
                
                rows = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description]
                
                if not rows:
                    self.log(f"Table {table_name} is empty")
                    continue
                
                # Map client data to global schema
                loaded_count = 0
                for row in rows:
                    row_dict = dict(zip(column_names, row))
                    
                    try:
                        # Extract relevant fields
                        customer_id = row_dict.get('customer_id')
                        recency = row_dict.get('recency')
                        frequency = row_dict.get('frequency')
                        monetary = row_dict.get('monetary')
                        r_score = row_dict.get('r_score')
                        f_score = row_dict.get('f_score')
                        m_score = row_dict.get('m_score')
                        rfm_score = row_dict.get('rfm_score')
                        rfm_segment = row_dict.get('rfm_segment')
                        
                        # First, get the global_customer_id
                        global_cursor.execute(sql.SQL("""
                            SELECT global_customer_id FROM {}.global_customers
                            WHERE client_id = %s AND source_customer_id = %s
                        """).format(sql.Identifier(schema)), 
                        (self.client_id, str(customer_id)))
                        
                        result = global_cursor.fetchone()
                        
                        if result:
                            global_customer_id = result[0]
                            
                            # Insert into global_rfm_segments table
                            global_cursor.execute(sql.SQL("""
                                INSERT INTO {}.global_rfm_segments 
                                (global_customer_id, client_id, recency_days, frequency_count,
                                 monetary_value, r_score, f_score, m_score, rfm_score,
                                 rfm_segment, segment_date, data_source, sync_date)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (global_customer_id, segment_date) 
                                DO UPDATE SET
                                    recency_days = EXCLUDED.recency_days,
                                    frequency_count = EXCLUDED.frequency_count,
                                    monetary_value = EXCLUDED.monetary_value,
                                    r_score = EXCLUDED.r_score,
                                    f_score = EXCLUDED.f_score,
                                    m_score = EXCLUDED.m_score,
                                    rfm_score = EXCLUDED.rfm_score,
                                    rfm_segment = EXCLUDED.rfm_segment,
                                    updated_at = CURRENT_TIMESTAMP
                            """).format(sql.Identifier(schema)), 
                            (
                                global_customer_id,
                                self.client_id,
                                recency,
                                frequency,
                                monetary,
                                r_score,
                                f_score,
                                m_score,
                                rfm_score,
                                rfm_segment,
                                self.sync_date,
                                f"rfm_{table_name}",
                                self.sync_date
                            ))
                            
                            loaded_count += 1
                        
                    except Exception as e:
                        self.log(f"Failed to process RFM row: {str(e)}", "ERROR")
                        continue
                
                self.log(f"Loaded {loaded_count} RFM records from {table_name}")
                total_loaded += loaded_count
            
            cursor.close()
            global_cursor.close()
            
            return total_loaded
            
        except Exception as e:
            self.log(f"Failed to load RFM data: {str(e)}", "ERROR")
            return 0
    
    def load_transaction_data(self):
        """Load transaction data from client DW to Global_DW."""
        try:
            cursor = self.client_conn.cursor()
            global_cursor = self.global_conn.cursor()
            schema = GLOBAL_DW_CONFIG['schema']
            
            # Find transaction tables in client DW
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'analytics' 
                AND (table_name LIKE '%online_retail%' OR table_name LIKE '%transaction%')
                ORDER BY table_name
            """)
            
            tables = cursor.fetchall()
            
            if not tables:
                self.log("No transaction tables found in client DW")
                return 0
            
            total_loaded = 0
            
            for table_row in tables:
                table_name = table_row[0]
                self.log(f"Processing transaction table: {table_name}")
                
                # Get data from client DW
                cursor.execute(sql.SQL("SELECT * FROM analytics.{}").format(
                    sql.Identifier(table_name)
                ))
                
                rows = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description]
                
                if not rows:
                    self.log(f"Table {table_name} is empty")
                    continue
                
                # Map client data to global schema
                loaded_count = 0
                for row in rows:
                    row_dict = dict(zip(column_names, row))
                    
                    try:
                        # Extract relevant fields
                        customer_id = row_dict.get('customer_id')
                        invoice = row_dict.get('invoice')
                        quantity = row_dict.get('quantity')
                        price = row_dict.get('price')
                        total_amount = quantity * price if quantity and price else None
                        
                        # First, get the global_customer_id
                        global_cursor.execute(sql.SQL("""
                            SELECT global_customer_id FROM {}.global_customers
                            WHERE client_id = %s AND source_customer_id = %s
                        """).format(sql.Identifier(schema)), 
                        (self.client_id, str(customer_id)))
                        
                        result = global_cursor.fetchone()
                        
                        if result:
                            global_customer_id = result[0]
                            
                            # Insert into global_transactions table
                            global_cursor.execute(sql.SQL("""
                                INSERT INTO {}.global_transactions 
                                (global_customer_id, client_id, invoice_number,
                                 quantity, unit_price, total_amount, data_source, sync_date)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """).format(sql.Identifier(schema)), 
                            (
                                global_customer_id,
                                self.client_id,
                                invoice,
                                quantity,
                                price,
                                total_amount,
                                f"transaction_{table_name}",
                                self.sync_date
                            ))
                            
                            loaded_count += 1
                        
                    except Exception as e:
                        self.log(f"Failed to process transaction row: {str(e)}", "ERROR")
                        continue
                
                self.log(f"Loaded {loaded_count} transactions from {table_name}")
                total_loaded += loaded_count
            
            cursor.close()
            global_cursor.close()
            
            return total_loaded
            
        except Exception as e:
            self.log(f"Failed to load transaction data: {str(e)}", "ERROR")
            return 0
    
    def load_interaction_data(self):
        """Load interaction data from client DW to Global_DW."""
        try:
            cursor = self.client_conn.cursor()
            global_cursor = self.global_conn.cursor()
            schema = GLOBAL_DW_CONFIG['schema']
            
            # Find interaction tables in client DW
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'analytics' 
                AND (table_name LIKE '%interaction%' OR table_name LIKE '%retailrocket%')
                ORDER BY table_name
            """)
            
            tables = cursor.fetchall()
            
            if not tables:
                self.log("No interaction tables found in client DW")
                return 0
            
            total_loaded = 0
            
            for table_row in tables:
                table_name = table_row[0]
                self.log(f"Processing interaction table: {table_name}")
                
                # Get data from client DW
                cursor.execute(sql.SQL("SELECT * FROM analytics.{}").format(
                    sql.Identifier(table_name)
                ))
                
                rows = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description]
                
                if not rows:
                    self.log(f"Table {table_name} is empty")
                    continue
                
                # Map client data to global schema
                loaded_count = 0
                for row in rows:
                    row_dict = dict(zip(column_names, row))
                    
                    try:
                        # Extract relevant fields
                        visitorid = row_dict.get('visitorid')
                        interaction_score = row_dict.get('interaction_score')
                        event = row_dict.get('event')
                        
                        # First, get the global_customer_id
                        global_cursor.execute(sql.SQL("""
                            SELECT global_customer_id FROM {}.global_customers
                            WHERE client_id = %s AND source_customer_id = %s
                        """).format(sql.Identifier(schema)), 
                        (self.client_id, str(visitorid)))
                        
                        result = global_cursor.fetchone()
                        
                        if result:
                            global_customer_id = result[0]
                            
                            # Insert into global_interactions table
                            global_cursor.execute(sql.SQL("""
                                INSERT INTO {}.global_interactions 
                                (global_customer_id, client_id, interaction_type,
                                 interaction_score, data_source, sync_date)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """).format(sql.Identifier(schema)), 
                            (
                                global_customer_id,
                                self.client_id,
                                event,
                                interaction_score,
                                f"interaction_{table_name}",
                                self.sync_date
                            ))
                            
                            loaded_count += 1
                        
                    except Exception as e:
                        self.log(f"Failed to process interaction row: {str(e)}", "ERROR")
                        continue
                
                self.log(f"Loaded {loaded_count} interactions from {table_name}")
                total_loaded += loaded_count
            
            cursor.close()
            global_cursor.close()
            
            return total_loaded
            
        except Exception as e:
            self.log(f"Failed to load interaction data: {str(e)}", "ERROR")
            return 0
    
    def load_churn_data(self):
        """Load churn data from client DW to Global_DW."""
        try:
            cursor = self.client_conn.cursor()
            global_cursor = self.global_conn.cursor()
            schema = GLOBAL_DW_CONFIG['schema']
            
            # Find churn tables in client DW
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'analytics' 
                AND table_name LIKE '%churn%'
                ORDER BY table_name
            """)
            
            tables = cursor.fetchall()
            
            if not tables:
                self.log("No churn tables found in client DW")
                return 0
            
            total_loaded = 0
            
            for table_row in tables:
                table_name = table_row[0]
                self.log(f"Processing churn table: {table_name}")
                
                # Get data from client DW
                cursor.execute(sql.SQL("SELECT * FROM analytics.{}").format(
                    sql.Identifier(table_name)
                ))
                
                rows = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description]
                
                if not rows:
                    self.log(f"Table {table_name} is empty")
                    continue
                
                # Map client data to global schema
                loaded_count = 0
                for row in rows:
                    row_dict = dict(zip(column_names, row))
                    
                    try:
                        # Extract relevant fields
                        customerid = row_dict.get('customerid')
                        churn = row_dict.get('churn')
                        tenure = row_dict.get('tenure')
                        
                        # First, get the global_customer_id
                        global_cursor.execute(sql.SQL("""
                            SELECT global_customer_id FROM {}.global_customers
                            WHERE client_id = %s AND source_customer_id = %s
                        """).format(sql.Identifier(schema)), 
                        (self.client_id, str(customerid)))
                        
                        result = global_cursor.fetchone()
                        
                        if result:
                            global_customer_id = result[0]
                            
                            # Insert into global_churn_metrics table
                            global_cursor.execute(sql.SQL("""
                                INSERT INTO {}.global_churn_metrics 
                                (global_customer_id, client_id, churn_status,
                                 tenure_days, data_source, sync_date)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                ON CONFLICT (global_customer_id) 
                                DO UPDATE SET
                                    churn_status = EXCLUDED.churn_status,
                                    tenure_days = EXCLUDED.tenure_days,
                                    updated_at = CURRENT_TIMESTAMP
                            """).format(sql.Identifier(schema)), 
                            (
                                global_customer_id,
                                self.client_id,
                                churn == 1 if churn is not None else None,
                                tenure,
                                f"churn_{table_name}",
                                self.sync_date
                            ))
                            
                            loaded_count += 1
                        
                    except Exception as e:
                        self.log(f"Failed to process churn row: {str(e)}", "ERROR")
                        continue
                
                self.log(f"Loaded {loaded_count} churn records from {table_name}")
                total_loaded += loaded_count
            
            cursor.close()
            global_cursor.close()
            
            return total_loaded
            
        except Exception as e:
            self.log(f"Failed to load churn data: {str(e)}", "ERROR")
            return 0
    
    def log_sync(self, sync_type, table_name, records_processed, 
                 records_inserted, records_updated, records_failed, 
                 start_time, end_time, status, error_message=None):
        """Log synchronization activity."""
        try:
            cursor = self.global_conn.cursor()
            schema = GLOBAL_DW_CONFIG['schema']
            
            cursor.execute(sql.SQL("""
                INSERT INTO {}.data_sync_log 
                (client_id, sync_type, table_name, records_processed,
                 records_inserted, records_updated, records_failed,
                 start_time, end_time, status, error_message, sync_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """).format(sql.Identifier(schema)), 
            (
                self.client_id,
                sync_type,
                table_name,
                records_processed,
                records_inserted,
                records_updated,
                records_failed,
                start_time,
                end_time,
                status,
                error_message,
                self.sync_date
            ))
            
            cursor.close()
            
        except Exception as e:
            self.log(f"Failed to log sync activity: {str(e)}", "ERROR")
    
    def load_client_data(self, client_id, client_name, client_code, 
                         industry=None, country=None):
        """Load all data from a client DW to Global_DW."""
        start_time = datetime.now()
        
        print("=" * 60)
        print("CUSTOMERDNA AI - LOAD DATA TO GLOBAL DATA WAREHOUSE")
        print("=" * 60)
        print(f"Client: {client_name} (ID: {client_id}, Code: {client_code})")
        print(f"Sync Date: {self.sync_date}")
        print("=" * 60)
        
        # Step 1: Connect to Global DW
        if not self.connect_to_global_dw():
            self.log_sync(
                sync_type="full_load",
                table_name="all",
                records_processed=0,
                records_inserted=0,
                records_updated=0,
                records_failed=0,
                start_time=start_time,
                end_time=datetime.now(),
                status="failed",
                error_message="Failed to connect to Global DW"
            )
            return False
        
        # Step 2: Connect to Client DW
        if not self.connect_to_client_dw(client_id):
            self.log_sync(
                sync_type="full_load",
                table_name="all",
                records_processed=0,
                records_inserted=0,
                records_updated=0,
                records_failed=0,
                start_time=start_time,
                end_time=datetime.now(),
                status="failed",
                error_message=f"Failed to connect to client {client_id} DW"
            )
            return False
        
        # Step 3: Get or create client record
        client_record_id = self.get_or_create_client(
            client_name, client_code, industry, country
        )
        
        if not client_record_id:
            self.log_sync(
                sync_type="full_load",
                table_name="all",
                records_processed=0,
                records_inserted=0,
                records_updated=0,
                records_failed=0,
                start_time=start_time,
                end_time=datetime.now(),
                status="failed",
                error_message="Failed to get/create client record"
            )
            return False
        
        # Step 4: Load customer personality data
        self.log("\nLoading customer personality data...")
        customer_count = self.load_customer_personality_data()
        
        # Step 5: Load RFM data
        self.log("\nLoading RFM segmentation data...")
        rfm_count = self.load_rfm_data()
        
        # Step 6: Load transaction data
        self.log("\nLoading transaction data...")
        transaction_count = self.load_transaction_data()
        
        # Step 7: Load interaction data
        self.log("\nLoading interaction data...")
        interaction_count = self.load_interaction_data()
        
        # Step 8: Load churn data
        self.log("\nLoading churn data...")
        churn_count = self.load_churn_data()
        
        end_time = datetime.now()
        
        # Calculate totals
        total_processed = customer_count + rfm_count + transaction_count + interaction_count + churn_count
        
        # Log the sync
        self.log_sync(
            sync_type="full_load",
            table_name="all",
            records_processed=total_processed,
            records_inserted=total_processed,  # Assuming all are inserts for now
            records_updated=0,
            records_failed=0,
            start_time=start_time,
            end_time=end_time,
            status="completed"
        )
        
        # Print summary
        print("\n" + "=" * 60)
        print("LOADING SUMMARY")
        print("=" * 60)
        print(f"Client: {client_name} (ID: {client_record_id})")
        print(f"Sync Date: {self.sync_date}")
        print(f"Duration: {(end_time - start_time).total_seconds():.2f} seconds")
        print("\nRecords loaded by category:")
        print(f"  • Customer Personality: {customer_count:,}")
        print(f"  • RFM Segmentation: {rfm_count:,}")
        print(f"  • Transactions: {transaction_count:,}")
        print(f"  • Interactions: {interaction_count:,}")
        print(f"  • Churn Metrics: {churn_count:,}")
        print(f"  • Total: {total_processed:,}")
        
        print("\n" + "=" * 60)
        print("LOADING COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
        return True

def main():
    """Main function."""
    loader = GlobalDWLoader(verbose=True)
    
    # For now, load data from client 1
    # You can extend this to load from multiple clients
    success = loader.load_client_data(
        client_id="1",
        client_name="Client 1",
        client_code="CLIENT_001",
        industry="Retail/E-commerce",
        country="Global"
    )
    
    if success:
        print("\n[SUCCESS] Data loaded to Global Data Warehouse!")
        print("\nNext steps:")
        print("  1. Add more clients as they become available")
        print("  2. Schedule regular syncs (will be done with Apache Airflow)")
        print("  3. Build cross-client analytics on top of Global_DW")
        return 0
    else:
        print("\n[ERROR] Data loading failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())