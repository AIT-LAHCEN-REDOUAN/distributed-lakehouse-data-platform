"""
Test script to verify .gitignore covers all dataset and preprocessed directories
"""

import os
import fnmatch

def test_gitignore_patterns():
    """Test if .gitignore patterns match the actual directories."""
    print("=" * 80)
    print("TESTING .gitignore COVERAGE")
    print("=" * 80)
    
    # Read .gitignore patterns
    gitignore_path = os.path.join(os.path.dirname(__file__), '.gitignore')
    with open(gitignore_path, 'r') as f:
        patterns = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    # Directories that should be ignored
    directories_to_check = [
        # Original datasets
        'CustomerDNA AI/datasets/',
        'CustomerDNA AI/datasets/client_1/',
        'CustomerDNA AI/datasets/client_1/Customer_Personality_Analysis/',
        'CustomerDNA AI/datasets/client_1/E-commerce_customer_churn/',
        'CustomerDNA AI/datasets/client_1/Retailrocket_recommender_system_dataset/',
        'CustomerDNA AI/datasets/client_1/UCI_Online_Retail_2/',
        'CustomerDNA AI/datasets/client_1/power_bi_dataset_loading/',
        
        # Preprocessed data
        'CustomerDNA AI/src/Preprocessing/client_1/Customer_Personality_Analysis_dataset_Preprocessing/cleaned_dataset/',
        'CustomerDNA AI/src/Preprocessing/client_1/E-commerce_customer_churn_Preprocessing/cleaned_dataset/',
        'CustomerDNA AI/src/Preprocessing/client_1/Retailrocket_recommender_system_dataset_Preprocessing/cleaned_dataset/',
        'CustomerDNA AI/src/Preprocessing/client_1/UCI_Online_Retail_2_Preprocessing/cleaned_dataset/',
        
        # EDA outputs
        'CustomerDNA AI/src/EDA/client_1/Customer_Personality_Analysis_dataset_EDA/output/',
        'CustomerDNA AI/src/EDA/client_1/E-commerce_customer_churn_EDA/output/',
        'CustomerDNA AI/src/EDA/client_1/Retailrocket_recommender_system_dataset_EDA/output/',
        'CustomerDNA AI/src/EDA/client_1/UCI_Online_Retail_2_EDA/output/',
        
        # Logs
        'CustomerDNA AI/src/EDA/client_1/Customer_Personality_Analysis_dataset_EDA/logs/',
        'CustomerDNA AI/src/Preprocessing/client_1/Customer_Personality_Analysis_dataset_Preprocessing/logs/',
        'CustomerDNA AI/src/ETL/DataWarehouse/logs/',
        
        # Old directories (for backward compatibility)
        '/dataset',
        'CustomerDNA AI/base_dataset/',
        'CustomerDNA AI/project_requirements/',
    ]
    
    print("\nTesting patterns against directories that should be ignored:")
    print("-" * 80)
    
    all_passed = True
    
    for directory in directories_to_check:
        matched = False
        for pattern in patterns:
            # Check if pattern matches directory
            if fnmatch.fnmatch(directory, pattern) or fnmatch.fnmatch(directory + '/', pattern):
                matched = True
                break
        
        if matched:
            print(f"[✓] {directory}")
        else:
            print(f"[✗] {directory} - NOT COVERED!")
            all_passed = False
    
    # Test file patterns
    print("\nTesting file patterns that should be ignored:")
    print("-" * 80)
    
    files_to_check = [
        'test.zip',
        'backup.tar',
        'data.gz',
        'archive.7z',
        'compressed.rar',
        'temp.tmp',
        'swap.swp',
        'config.env',
        'secrets.key',
        'database.dump',
        'report.pbix',
        'credentials.cnf',
    ]
    
    for file in files_to_check:
        matched = False
        for pattern in patterns:
            if fnmatch.fnmatch(file, pattern):
                matched = True
                break
        
        if matched:
            print(f"[✓] {file}")
        else:
            print(f"[✗] {file} - NOT COVERED!")
            all_passed = False
    
    return all_passed

def check_actual_directories():
    """Check if actual directories exist and would be ignored."""
    print("\n" + "=" * 80)
    print("CHECKING ACTUAL DIRECTORY EXISTENCE")
    print("=" * 80)
    
    base_path = os.path.join(os.path.dirname(__file__), 'CustomerDNA AI')
    
    directories_to_verify = [
        ('datasets/', 'Original datasets'),
        ('datasets/client_1/', 'Client 1 datasets'),
        ('src/Preprocessing/client_1/', 'Client 1 preprocessing'),
        ('src/EDA/client_1/', 'Client 1 EDA'),
        ('src/ETL/DataWarehouse/', 'Global Data Warehouse'),
    ]
    
    print("\nChecking if directories exist:")
    print("-" * 80)
    
    all_exist = True
    
    for dir_path, description in directories_to_verify:
        full_path = os.path.join(base_path, dir_path)
        if os.path.exists(full_path):
            print(f"[✓] {dir_path} - {description}")
        else:
            print(f"[✗] {dir_path} - {description} - DOES NOT EXIST")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("CUSTOMERDNA AI - .gitignore VERIFICATION")
    print("=" * 80)
    
    tests = [
        ("Pattern Coverage", test_gitignore_patterns),
        ("Directory Existence", check_actual_directories),
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
        print("\n[SUCCESS] .gitignore is properly configured!")
        print("All datasets, preprocessed files, and logs will be excluded from Git.")
        return 0
    else:
        print("\n[WARNING] Some tests failed. Please check the .gitignore file.")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())