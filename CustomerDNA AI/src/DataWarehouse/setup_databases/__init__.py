"""
CustomerDNA AI - Data Warehouse Module
Dual database architecture for raw data storage and analytical processing.
"""

__version__ = "1.0.0"
__author__ = "CustomerDNA AI Team"

# Core modules
from . import config
from . import setup_databases
from . import load_to_base_db
from . import sync_databases
from . import simple_test

__all__ = [
    'config',
    'setup_databases',
    'load_to_base_db',
    'sync_databases',
    'simple_test'
]