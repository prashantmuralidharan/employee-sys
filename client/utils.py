
"""
Utility functions for the client application.
"""
from typing import List, Dict, Any, Optional
from typing import Callable
from datetime import datetime
import os
import csv
import json
import re
import logging

# Get client logger
logger = logging.getLogger("client")


def read_csv_data(file_path: str) -> List[Dict[str, Any]]:
    """
    Read employee data from a CSV file.

    Args:
        file_path (str): Path to the CSV file

    Returns:
        List[Dict[str, Any]]: List of dictionaries containing employee data
    """
    employees = []

    # Check if file exists
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return []

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            # Validate headers
            if reader.fieldnames is None or not all(reader.fieldnames):
                logger.error("CSV file is empty or missing headers")
                return []

            for i, row in enumerate(reader, start=1):
                try:
                    # Clean up data (trim whitespace, remove empty values)
                    cleaned_row = {
                        key.strip(): value.strip() if isinstance(value, str) else value
                        for key, value in row.items()
                    }

                    # Ensure row is not empty
                    if any(cleaned_row.values()):
                        employees.append(cleaned_row)
                    else:
                        logger.warning(f"Skipping empty row {i}")

                except Exception as row_error:
                    logger.error(f"Error processing row {i}: {row_error}")

        if not employees:
            logger.warning(f"No valid records found in {file_path}")

        logger.info(f"Successfully read {len(employees)} records from {file_path}")
        return employees

    except Exception as e:
        logger.error(f"Error reading CSV file {file_path}: {e}")
        return []


def validate_employee_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate an employee record and return validation results.

    Args:
        record (dict): Employee record to validate

    Returns:
        dict: Dictionary with validation results including errors
    """
    errors = []

    # Check required fields
    required_fields = ["employee_id", "name", "email", "department",
                       "designation", "salary", "date_of_joining"]

    for field in required_fields:
        if field not in record or not record[field]:
            errors.append(f"Missing required field: {field}")

    # Validate email format
    if "email" in record and record["email"]:
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, record["email"]):
            errors.append("Invalid email format")

    # Validate salary (should be a positive number)
    if "salary" in record and record["salary"]:
        try:
            salary = float(record["salary"])
            if salary <= 0:
                errors.append("Salary must be positive")
        except ValueError:
            errors.append("Salary must be a numeric value")

    # Validate date format
    if "date_of_joining" in record and record["date_of_joining"]:
        try:
            datetime.strptime(record["date_of_joining"], "%Y-%m-%d")
        except ValueError:
            errors.append("Invalid date format for date_of_joining. Expected format: YYYY-MM-DD")

    # Return validation result
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "record": record
    }


def prepare_record_for_transmission(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare an employee record for transmission to the server.

    Args:
        record (dict): Employee record to prepare

    Returns:
        dict: Prepared record ready for transmission
    """
    prepared = record.copy()

    # Format date fields if needed
    if "date_of_joining" in prepared and prepared["date_of_joining"]:
        try:
            date_obj = datetime.strptime(prepared["date_of_joining"], "%Y-%m-%d")
            prepared["date_of_joining"] = date_obj.strftime("%Y-%m-%d")
        except ValueError:
            pass  # Leave as is if parsing fails

    # Convert numeric fields
    if "salary" in prepared and prepared["salary"]:
        try:
            prepared["salary"] = float(prepared["salary"])
        except ValueError:
            pass  # Leave as is if conversion fails

    # Add metadata for transmission
    prepared["_client_timestamp"] = datetime.now().isoformat()

    return prepared


def chunk_records(records: List[Dict[str, Any]], batch_size: int) -> List[List[Dict[str, Any]]]:
    """
    Split records into batches of specified size.

    Args:
        records (list): List of employee records
        batch_size (int): Size of each batch

    Returns:
        list: List of batches
    """
    return [records[i:i + batch_size] for i in range(0, len(records), batch_size)]


def async_timer_decorator(func: Callable) -> Callable:
    """
    Decorator to time async functions.

    Args:
        func (callable): Async function to wrap

    Returns:
        callable: Wrapped function with timing functionality
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = datetime.now()
        result = await func(*args, **kwargs)
        end_time = datetime.now()
        logger.info(f"{func.__name__} completed in {(end_time - start_time).total_seconds():.2f} seconds")
        return result
    return wrapper


def format_error_message(message: str) -> str:
    """
    Format error messages for consistent display.

    Args:
        message (str): Error message to format

    Returns:
        str: Formatted error message
    """
    return f"ERROR: {message}"


def save_to_json(data: List[Dict[str, Any]], file_path: str) -> bool:
    """
    Save data to a JSON file.

    Args:
        data (list): Data to save
        file_path (str): Path to save the JSON file

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Successfully saved data to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving data to JSON: {e}")
        return False
