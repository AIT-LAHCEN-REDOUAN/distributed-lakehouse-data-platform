"""
CustomerDNA AI - Global Data Warehouse Structure Test
Description: Test script to verify the global DataWarehouse structure and integration
"""

import os
import sys

def test_directory_structure():
    """Test if the required directory structure exists."""
    print("=" * 80)
    print("TESTING GLOBAL DATA WAREHOUSE DIRECTORY STRUCTURE")
    print("=" * 80)
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    required_dirs = [
        'config',
        'scripts', 
        'logs',
        'docs'
    ]
    
    all_passed = True
    
    for dir_name in required_dirs:
        dir_path = os.path.join(base_path, dir_name)
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            print(f"[✓] {dir_name}/ directory exists")
        else:
            print(f"[✗] {dir_name}/ directory missing")
            all_passed = False
    
    # Test config files
    config_files = [
        'global_config.py'
    ]
    
    config_dir = os.path.join(base_path, 'config')
    for file_name in config_files:
        file_path = os.path.join(config_dir, file_name)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            print(f"[✓] config/{file_name} exists")
        else:
            print(f"[✗] config/{file_name} missing")
            all_passed = False
    
    return all_passed

def test_client_integration():
    """Test integration with client database setup."""
    print("\n" + "=" * 80)
    print("TESTING CLIENT DATABASE INTEGRATION")
    print("=" * 80)
    
    # Get project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    # Test client setup directory
    client_setup_dir = os.path.join(project_root, 'src', 'ETL', 'setup_database_for_each_clients_datasets')
    
    if not os.path.exists(client_setup_dir):
        print("[✗] Client setup directory not found")
        return False
    
    print(f"[✓] Client setup directory exists: {os.path.basename(client_setup_dir)}/")
    
    # Check for client directories
    client_dirs = []
    for item in os.listdir(client_setup_dir):
        item_path = os.path.join(client_setup_dir, item)
        if os.path.isdir(item_path) and item.startswith('client_'):
            client_dirs.append(item)
    
    if client_dirs:
        print(f"[✓] Found {len(client_dirs)} client directory(ies): {', '.join(client_dirs)}")
        
        # Test client_1 configuration
        client_1_dir = os.path.join(client_setup_dir, 'client_1')
        if os.path.exists(client_1_dir):
            required_files = ['config.py', 'setup_databases.py', 'load_to_base_db.py', 'sync_databases.py']
            for file_name in required_files:
                file_path = os.path.join(client_1_dir, file_name)
                if os.path.exists(file_path):
                    print(f"[✓] client_1/{file_name} exists")
                else:
                    print(f"[✗] client_1/{file_name} missing")
                    return False
    else:
        print("[✗] No client directories found")
        return False
    
    return True

def test_template_structure():
    """Test if client template exists."""
    print("\n" + "=" * 80)
    print("TESTING CLIENT TEMPLATE STRUCTURE")
    print("=" * 80)
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    template_dir = os.path.join(project_root, 'src', 'ETL', 'setup_database_for_each_clients_datasets', 'client_template')
    
    if not os.path.exists(template_dir):
        print("[✗] Client template directory not found")
        return False
    
    print(f"[✓] Client template directory exists")
    
    # Check template files
    template_files = ['config.py', '__init__.py']
    for file_name in template_files:
        file_path = os.path.join(template_dir, file_name)
        if os.path.exists(file_path):
            print(f"[✓] client_template/{file_name} exists")
        else:
            print(f"[✗] client_template/{file_name} missing")
            return False
    
    return True

def test_path_resolution():
    """Test path resolution between global and client structures."""
    print("\n" + "=" * 80)
    print("TESTING PATH RESOLUTION")
    print("=" * 80)
    
    try:
        # Try to import global config
        sys.path.append(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config'
        ))
        
        from global_config import (
            get_client_database_name,
            get_client_dw_database_name
        )
        
        # Test function calls
        client_db_name = get_client_database_name("client_1")
        client_dw_name = get_client_dw_database_name("client_1")
        
        print(f"[✓] Global config imported successfully")
        print(f"[✓] Client 1 Base DB name: {client_db_name}")
        print(f"[✓] Client 1 DW name: {client_dw_name}")
        
        return True
        
    except ImportError as e:
        print(f"[✗] Failed to import global config: {e}")
        return False
    except Exception as e:
        print(f"[✗] Error in path resolution: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("CUSTOMERDNA AI - GLOBAL DATA WAREHOUSE STRUCTURE VALIDATION")
    print("=" * 80)
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Client Integration", test_client_integration),
        ("Template Structure", test_template_structure),
        ("Path Resolution", test_path_resolution)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"[✗] Test '{test_name}' failed with error: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed_count = 0
    total_count = len(results)
    
    for test_name, passed in results:
        status = "PASSED" if passed else "FAILED"
        symbol = "✓" if passed else "✗"
        print(f"{symbol} {test_name}: {status}")
        if passed:
            passed_count += 1
    
    print("\n" + "-" * 80)
    print(f"RESULTS: {passed_count}/{total_count} tests passed")
    print("=" * 80)
    
    if passed_count == total_count:
        print("\n[SUCCESS] Global Data Warehouse structure is properly configured!")
        return 0
    else:
        print("\n[WARNING] Some tests failed. Please check the structure.")
        return 1

if __name__ == "__main__":
    sys.exit(main())