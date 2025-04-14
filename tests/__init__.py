"""
Test suite initialization for Employee Record System
"""

import logging
import pytest

# Configure test logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[TEST] %(asctime)s - %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Global test configuration
TEST_CONFIG = {
    'num_test_records': 100,
    'test_database': 'test_employee_records',
    'timeout': 30  # seconds
}

def pytest_configure(config):
    """
    Pytest configuration hook
    """
    logger.info("Configuring test suite for Employee Record System")
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers",
        "performance: mark test as a performance test"
    )

def pytest_runtest_setup(item):
    """
    Setup method for each test
    """
    logger.info(f"Setting up test: {item.name}")

def pytest_runtest_teardown(item, nextitem):
    """
    Teardown method for each test
    """
    logger.info(f"Tearing down test: {item.name}")