"""
CustomerDNA AI - Data Ingestion Orchestration Script
Purpose: Run all dataset ingestion scripts sequentially with progress tracking
"""

import os
import sys
import time
from datetime import datetime, timezone
import threading
import queue

from tqdm import tqdm

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MONITORING_SRC_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "monitoring")
)
if MONITORING_SRC_DIR not in sys.path:
    sys.path.append(MONITORING_SRC_DIR)

try:
    from shared.pipeline_metrics import record_ingestion_run
except Exception:
    record_ingestion_run = None


def run_ingestion(script_name, dataset_name=None, progress_queue=None):
    """Run a specific ingestion script with progress tracking."""
    start_time = time.time()

    try:
        # Import and run the script
        if script_name == "ingest_customer_personality.py":
            from ingest_customer_personality import CustomerPersonalityIngestorSimple
            ingestor = CustomerPersonalityIngestorSimple()
            result = ingestor.run_ingestion()

        elif script_name == "ingest_ecommerce_churn.py":
            from ingest_ecommerce_churn import EcommerceChurnIngestorSimple
            ingestor = EcommerceChurnIngestorSimple()
            result = ingestor.run_ingestion()

        elif script_name == "ingest_retailrocket.py":
            from ingest_retailrocket import RetailRocketIngestorSimple
            ingestor = RetailRocketIngestorSimple()
            result = ingestor.run_ingestion()

        elif script_name == "ingest_uci_online_retail.py":
            from ingest_uci_online_retail import UCIOnlineRetailIngestorSimple
            ingestor = UCIOnlineRetailIngestorSimple()
            result = ingestor.run_ingestion()

        else:
            print(f"ERROR: Unknown script: {script_name}")
            return False

        end_time = time.time()
        duration = end_time - start_time

        # Handle different return types
        if isinstance(result, dict):
            # Dictionary return type (customer_personality, ecommerce_churn)
            success = result.get('success', False)
            records = result.get('records_processed', 0)
            output_path = result.get('csv_path', 'N/A')
        else:
            # Boolean return type (retailrocket, uci_online_retail)
            success = result
            records = 0  # Can't get record count from boolean
            output_path = 'N/A'

        if success:
            if progress_queue:
                progress_queue.put({
                    'script': script_name,
                    'status': 'success',
                    'duration': duration,
                    'records': records,
                    'output': output_path
                })
            return True
        else:
            if progress_queue:
                progress_queue.put({
                    'script': script_name,
                    'status': 'failed',
                    'duration': duration,
                    'error': result.get('error', 'Script returned False') if isinstance(result, dict) else 'Script returned False'
                })
            return False

    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        if progress_queue:
            progress_queue.put({
                'script': script_name,
                'status': 'error',
                'duration': duration,
                'error': str(e)
            })
        return False


def main():
    """Main orchestration function with progress tracking."""
    run_started_at = datetime.now(timezone.utc)

    print("\n" + "="*80)
    print("CUSTOMERDNA AI - DATA INGESTION ORCHESTRATION")
    print("="*80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Scripts Directory: {os.path.dirname(os.path.abspath(__file__))}")
    print("="*80)

    # Define the ingestion scripts to run in order
    ingestion_scripts = [
        "ingest_customer_personality.py",
        "ingest_ecommerce_churn.py",
        "ingest_retailrocket.py",
        "ingest_uci_online_retail.py"
    ]

    print(f"\nWill run {len(ingestion_scripts)} ingestion scripts:")
    for i, script in enumerate(ingestion_scripts, 1):
        print(f"  {i}. {script}")

    print("\n" + "="*80)
    print("STARTING INGESTION PROCESS")
    print("="*80)

    # Create a queue for progress updates
    progress_queue = queue.Queue()
    results = []
    script_updates = {}
    total_start_time = time.time()

    print(f"\nProcessing {len(ingestion_scripts)} datasets:")

    # Create a progress bar
    with tqdm(total=len(ingestion_scripts), desc="Datasets", unit="dataset",
              bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:

        # Run all ingestion scripts
        for script in ingestion_scripts:
            script_start_time = time.time()

            # Update progress bar description
            pbar.set_description(f"Processing {script}")

            # Run ingestion in a separate thread to allow progress updates
            def run_script():
                success = run_ingestion(script, progress_queue=progress_queue)
                results.append((script, success))

            thread = threading.Thread(target=run_script)
            thread.start()

            # Wait for thread to complete with timeout
            thread.join(timeout=300)  # 5 minute timeout per dataset

            if thread.is_alive():
                print(f"\n[WARNING] {script} timed out after 5 minutes")
                results.append((script, False))
                progress_queue.put({
                    'script': script,
                    'status': 'timeout',
                    'duration': 300,
                    'error': 'Script timed out after 5 minutes'
                })

            script_end_time = time.time()
            script_duration = script_end_time - script_start_time

            # Update progress bar
            pbar.update(1)

            # Check for progress updates
            while not progress_queue.empty():
                update = progress_queue.get()
                script_name = update['script']
                status = update['status']
                duration = update['duration']
                script_updates[script_name] = update

                if status == 'success':
                    records = update['records']
                    output = update['output']
                    print(f"\n  [SUCCESS] {script_name}: SUCCESS ({duration:.2f}s, {records:,} records)")
                    print(f"     Output: {os.path.basename(output)}")
                elif status == 'failed':
                    error = update['error']
                    print(f"\n  [FAILED] {script_name}: FAILED ({duration:.2f}s)")
                    print(f"     Error: {error}")
                elif status == 'error':
                    error = update['error']
                    print(f"\n  [ERROR] {script_name}: ERROR ({duration:.2f}s)")
                    print(f"     Exception: {error}")
                elif status == 'timeout':
                    error = update['error']
                    print(f"\n  [TIMEOUT] {script_name}: TIMEOUT ({duration:.2f}s)")
                    print(f"     Error: {error}")

            # Small pause between scripts
            if script != ingestion_scripts[-1]:
                time.sleep(1)

    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    run_ended_at = datetime.now(timezone.utc)

    # Summary report
    print("\n" + "="*80)
    print("INGESTION ORCHESTRATION COMPLETE")
    print("="*80)
    print(f"Total Duration: {total_duration:.2f} seconds ({total_duration/60:.2f} minutes)")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    successful = sum(1 for _, success in results if success)
    failed = len(results) - successful

    print(f"\n[RESULTS SUMMARY]")
    print(f"  [SUCCESS] Successful: {successful}/{len(results)}")
    print(f"  [FAILED] Failed: {failed}/{len(results)}")

    print(f"\n[DETAILED RESULTS]")
    for i, (script, success) in enumerate(results, 1):
        status = "[SUCCESS]" if success else "[FAILED]"
        print(f"  {i}. {script}: {status}")

    # Timing breakdown
    print(f"\n[TIMING BREAKDOWN]")
    print(f"  Average per dataset: {total_duration/len(ingestion_scripts):.2f}s")
    print(f"  Total processing time: {total_duration:.2f}s")

    print("\n" + "="*80)
    print("[NEXT STEPS]")
    print("="*80)
    print("1. Check ingested_data folder for processed CSV files")
    print("2. Check logs folder for ingestion logs")
    print("3. Use ELT scripts to load data to client1_DB")
    print("4. Apply dbt transformations in client1_DW")
    print("="*80)

    # Return overall success (all must succeed)
    overall_success = all(success for _, success in results)

    if record_ingestion_run:
        dataset_summaries = []
        for script_name, success in results:
            update = script_updates.get(script_name, {})
            dataset_summaries.append(
                {
                    "script_name": script_name,
                    "status": "success" if success else "failed",
                    "duration_seconds": round(float(update.get("duration", 0.0)), 3),
                    "records_processed": int(update.get("records", 0) or 0),
                    "output_path": update.get("output", "N/A"),
                }
            )

        record_ingestion_run(
            {
                "status": "success" if overall_success else "failed",
                "started_at": run_started_at.isoformat(),
                "ended_at": run_ended_at.isoformat(),
                "duration_seconds": round(total_duration, 3),
                "successful_datasets": successful,
                "failed_datasets": failed,
                "datasets": dataset_summaries,
            }
        )

    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(main())
