"""
Client application for receiving and storing employee records.
"""
# client/client_main.py
import asyncio
import aiohttp
import argparse
import json
import logging
from typing import List, Dict, Any, Optional
import backoff
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[CLIENT] %(asctime)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Define constants directly in the client file
SERVER_URL = "http://127.0.0.1:8080"  # Updated to match the server's default port
API_KEY = "1993"  # Match the server's default API_KEY
BATCH_SIZE = 100  # Increased default batch size
MAX_RETRIES = 3
RETRY_DELAY = 1
CONCURRENCY_LIMIT = 10  # Increased concurrency limit


# Utility functions
def read_data_file(file_path):
    """Read data from a file, supporting both CSV and JSON formats."""
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == '.csv':
        return read_csv_data(file_path)
    elif file_extension == '.json':
        return read_json_data(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {file_extension}. Use .csv or .json")


def read_csv_data(file_path):
    """Read CSV data from a file."""
    import csv
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        data = list(reader)

        # Convert numeric fields to appropriate types
        for record in data:
            if 'Employee ID' in record and record['Employee ID'].isdigit():
                record['Employee ID'] = int(record['Employee ID'])
            if 'Salary' in record and record['Salary'].replace('.', '', 1).isdigit():
                record['Salary'] = float(record['Salary'])

        return data


def read_json_data(file_path):
    """Read JSON data from a file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
        # If data is already a list, return it
        if isinstance(data, list):
            # If it's a list of lists (where each inner list contains one record),
            # flatten it to a list of records
            if data and isinstance(data[0], list):
                return [record for sublist in data for record in sublist]
            return data
        # If it's a dictionary containing a list of records, return the list
        for key, value in data.items():
            if isinstance(value, list):
                return value
        # If it's a single record, return it as a list
        return [data]


def chunk_records(records, chunk_size):
    """Break records into chunks of specified size."""
    for i in range(0, len(records), chunk_size):
        yield records[i:i + chunk_size]


def async_timer_decorator(func):
    """Decorator to time async functions."""

    async def wrapper(*args, **kwargs):
        import time
        start = time.time()
        result = await func(*args, **kwargs)
        end = time.time()
        logger.info(f"Function {func.__name__} took {end - start:.2f} seconds to complete")
        return result

    return wrapper


class EmployeeClient:
    """Client for processing and sending employee records to the server."""

    def __init__(self, server_url: str = SERVER_URL, api_key: str = API_KEY):
        self.server_url = server_url
        self.api_key = api_key
        self.API_ENDPOINT = f"{server_url}/api/employees"  # Use the authenticated endpoint
        self.token = None
        self.headers = {
            "Content-Type": "application/json"
        }
        self.semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

    async def authenticate(self):
        """Get authentication token from the server."""
        auth_url = f"{self.server_url}/api/auth"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(auth_url, json={"api_key": self.api_key}) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.token = data.get("token")
                        self.headers["Authorization"] = f"Bearer {self.token}"
                        logger.info("Authentication successful")
                        return True
                    else:
                        logger.error(f"Authentication failed: {await response.text()}")
                        return False
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=MAX_RETRIES,
        factor=RETRY_DELAY
    )
    async def send_employee_batch(self, session, batch):
        """Send a batch of employee records to the server with retry logic."""
        async with self.semaphore:  # Prevent overwhelming the server
            try:
                # Debug the batch being sent
                if len(batch) == 1:
                    logger.info(f"Sending record: {json.dumps(batch[0])}")
                else:
                    logger.info(f"Sending batch of {len(batch)} records")

                async with session.post(self.API_ENDPOINT, json=batch, headers=self.headers,
                                        timeout=30) as response:
                    response_text = await response.text()
                    logger.info(f"Server response: {response.status} - {response_text}")

                    if response.status == 200:
                        response_data = await response.json()
                        return response_data
                    else:
                        logger.error(f"Failed to send batch: {response.status}: {response_text}")
                        return {"success": False, "success_count": 0, "error_count": len(batch)}
            except Exception as e:
                logger.error(f"Error sending employee batch: {e}")
                return {"success": False, "success_count": 0, "error_count": len(batch)}

    @async_timer_decorator
    async def process_file(self, file_path: str, batch_size: Optional[int] = None) -> Dict[str, Any]:
        """Process the data file and send records to the server in batches."""
        # First authenticate
        if not await self.authenticate():
            logger.error("Authentication failed - cannot proceed")
            return {"total_records": 0, "success_count": 0, "error_count": 0}

        # Then process the file
        try:
            records = read_data_file(file_path)
            logger.info(f"Successfully loaded {len(records)} records from {file_path}")
        except Exception as e:
            logger.error(f"Error loading data from {file_path}: {str(e)}")
            return {"total_records": 0, "success_count": 0, "error_count": 0}

        batch_size = batch_size or BATCH_SIZE

        # Calculate number of batches in advance
        num_batches = (len(records) + batch_size - 1) // batch_size  # Ceiling division
        logger.info(f"Processing {len(records)} records in {num_batches} batches")

        total_success_count = 0
        total_error_count = 0

        async with aiohttp.ClientSession() as session:
            for i, batch in enumerate(chunk_records(records, batch_size)):
                logger.info(f"Sending batch {i + 1} with {len(batch)} records")
                result = await self.send_employee_batch(session, batch)

                if result:
                    success_count = result.get("success_count", 0)
                    error_count = result.get("error_count", 0)

                    total_success_count += success_count
                    total_error_count += error_count

                    logger.info(f"Batch {i + 1} results: {success_count} success, {error_count} errors")

                    # Check if there were validation errors
                    if "validation_errors" in result and result["validation_errors"]:
                        logger.warning(f"Validation errors in batch {i + 1}:")
                        for error in result["validation_errors"]:
                            logger.warning(f"  Record {error['index']}: {error['error']}")
                else:
                    logger.error(f"Batch {i + 1} failed completely")
                    total_error_count += len(batch)

        return {
            "total_records": len(records),
            "success_count": total_success_count,
            "error_count": total_error_count
        }


async def main(file_path: str, batch_size: Optional[int] = None):
    """Main entry point for the client application."""
    client = EmployeeClient()
    result = await client.process_file(file_path, batch_size)
    logger.info(f"Processing complete: {json.dumps(result)}")
    print(f"Processing complete: {json.dumps(result)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Employee Record Client")
    parser.add_argument("--file-path", dest="file_path",
                        default=os.path.join("data", "employees.csv"),
                        help="Path to data file containing employee records (default: data/employees.csv)")
    parser.add_argument("--batch-size", type=int, help="Batch size for sending records")
    parser.add_argument("--all", action="store_true", help="Process all files in the data directory")
    parser.add_argument("--server-url", dest="server_url", default=SERVER_URL,
                        help=f"Server URL (default: {SERVER_URL})")

    args = parser.parse_args()

    if args.all:
        # Process all files in the data directory
        data_dir = "data"
        if not os.path.exists(data_dir):
            print(f"Error: Directory not found: {data_dir}")
            exit(1)

        file_paths = [os.path.join(data_dir, f) for f in os.listdir(data_dir)
                      if f.endswith(('.csv', '.json'))]

        if not file_paths:
            print(f"No .csv or .json files found in {data_dir}")
            exit(1)


        async def process_all_files():
            client = EmployeeClient(server_url=args.server_url)
            total_result = {"total_records": 0, "success_count": 0, "error_count": 0}

            for file_path in file_paths:
                print(f"Processing file: {file_path}")
                result = await client.process_file(file_path, args.batch_size)
                total_result["total_records"] += result["total_records"]
                total_result["success_count"] += result["success_count"]
                total_result["error_count"] += result["error_count"]

            print(f"All processing complete: {json.dumps(total_result)}")
            return total_result


        asyncio.run(process_all_files())
    else:
        # Check if file exists
        if not os.path.exists(args.file_path):
            print(f"Error: File not found: {args.file_path}")
            print("Please provide a valid file path with --file-path or create the default file.")
            exit(1)

        client = EmployeeClient(server_url=args.server_url)
        asyncio.run(main(args.file_path, args.batch_size))