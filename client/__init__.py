# -*- coding: utf-8 -*-
"""
Created on Thu Mar 27 14:09:33 2025

@author: mdrkm
"""

"""
Client-side initialization for Employee Record System
"""

import logging
from typing import List, Dict, Any

# Configure client-side logging
logging.basicConfig(
    level=logging.INFO,
    format='[CLIENT] %(asctime)s - %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Import key client-side modules
from .config import Config
from client.utils import (
    read_csv_data, 
    validate_employee_record, 
    prepare_record_for_transmission
)

# Client-side constants
CLIENT_NAME = "EmployeeRecordClient"
SUPPORTED_TRANSMISSION_MODES = ['http', 'kafka', 'websocket']

def initialize_client() -> None:
    """
    Initialize client-side configurations and perform pre-flight checks
    """
    logger.info(f"Initializing {CLIENT_NAME}")
    
    # Validate configuration
    assert Config.TRANSMISSION_MODE in SUPPORTED_TRANSMISSION_MODES, \
        f"Unsupported transmission mode: {Config.TRANSMISSION_MODE}"
    
    # Additional initialization logic can be added here
    logger.info(f"Client initialized with {Config.TRANSMISSION_MODE} mode")

# Perform initialization when module is imported
initialize_client()
