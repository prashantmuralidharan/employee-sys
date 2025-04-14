import os
import asyncio
import logging
import traceback
import functools
from typing import List, Dict, Any
from aiohttp import web
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import argparse
import json

# Load environment variables
load_dotenv()

# Set default values if environment variables are not set
JWT_SECRET = os.getenv("JWT_SECRET", "051993")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
API_KEY = os.getenv("API_KEY", "1993")

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="[SERVER] %(asctime)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


# Create a simple in-memory database for testing
class SimpleDatabase:
    def __init__(self):
        self.employees = []

    async def create_pool(self):
        logger.info("Simple database initialized")
        return True

    def set_config(self, config):
        logger.info(f"Database config set: {config}")
        return True

    async def close(self):
        logger.info("Database connection closed")
        return True

    async def insert_employees(self, employees):
        try:
            success_count = 0
            error_count = 0

            for employee in employees:
                try:
                    self.employees.append(employee)
                    success_count += 1
                except Exception:
                    error_count += 1

            logger.info(f"Inserted {success_count} employees, failed to insert {error_count}")
            return (success_count, error_count)
        except Exception as e:
            logger.error(f"Error inserting employees: {e}")
            return (0, len(employees))


# Create a simple Employee model
class Employee:
    def __init__(self, id, name, department, salary):
        self.id = id
        self.name = name
        self.department = department
        self.salary = salary


# Simple decorator for logging requests
def log_request(func):
    @functools.wraps(func)
    async def wrapper(request, *args, **kwargs):
        logger.info(f"Request to {request.path}: {request.method}")
        return await func(request, *args, **kwargs)

    return wrapper


# Simple decorator for timing execution
def async_log_execution_time(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        import time
        start = time.time()
        result = await func(*args, **kwargs)
        end = time.time()
        logger.info(f"Function {func.__name__} took {end - start:.2f} seconds to complete")
        return result

    return wrapper


# Create database instance
db = SimpleDatabase()


def generate_jwt_token(api_key: str) -> str:
    """Generate a JWT token for API authentication."""
    try:
        payload = {
            "exp": datetime.utcnow() + timedelta(days=1),
            "iat": datetime.utcnow(),
            "sub": "api_access",
            "api_key": api_key
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        logger.info("JWT token generated successfully")
        return token
    except Exception as e:
        logger.error(f"JWT token generation failed: {str(e)}\n{traceback.format_exc()}")
        raise


def validate_jwt(func):
    """Custom JWT validation decorator."""

    @functools.wraps(func)
    async def wrapper(request: web.Request, *args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        logger.debug(f"Authorization header: {auth_header[:20]}...")  # Log first part for debugging

        if not auth_header.startswith("Bearer "):
            logger.warning("Missing or invalid Authorization header")
            return web.json_response({"error": "Invalid authorization token"}, status=401)

        token = auth_header.split("Bearer ")[-1]
        logger.debug(f"Token extracted: {token[:10]}...")  # Log first part for debugging

        try:
            decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            request["user"] = decoded_token  # Attach decoded token data to the request
            return await func(request, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            logger.warning("JWT Token expired")
            return web.json_response({"error": "Token expired"}, status=401)
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT Token: {str(e)}")
            return web.json_response({"error": "Invalid token"}, status=401)
        except Exception as e:
            logger.error(f"JWT validation error: {str(e)}\n{traceback.format_exc()}")
            return web.json_response({"error": f"Authentication error: {str(e)}"}, status=401)

    return wrapper


@log_request
async def authenticate(request: web.Request) -> web.Response:
    """Endpoint to authenticate and get a JWT token."""
    try:
        logger.info("Authentication request received")
        data = await request.json()
        logger.debug(f"Auth request data keys: {list(data.keys())}")

        if data.get("api_key") == API_KEY:
            token = generate_jwt_token(API_KEY)
            return web.json_response({"token": token}, status=200)
        logger.warning("Invalid API key provided.")
        return web.json_response({"error": "Invalid API key"}, status=401)
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}\n{traceback.format_exc()}")
        return web.json_response({"error": f"Server Error: {str(e)}"}, status=500)


@log_request
@validate_jwt
@async_log_execution_time
async def create_employees(request: web.Request) -> web.Response:
    """Endpoint to receive and store employee records."""
    try:
        logger.info("Employee data request received")

        # Ensure JSON is correctly parsed
        try:
            records = await request.json()
        except json.JSONDecodeError:
            logger.warning("Invalid JSON received in request body.")
            return web.json_response({
                "success": False,
                "error": "Invalid JSON format",
                "success_count": 0,
                "error_count": 1
            }, status=400)

        # Validate records is a list
        if not isinstance(records, list):
            logger.warning(f"Request body must be a list of employee records. Received type: {type(records)}")
            return web.json_response({
                "success": False,
                "error": "Expected a list of employee records",
                "success_count": 0,
                "error_count": 1
            }, status=400)

        logger.info(f"Received {len(records)} employee records")

        # Process the records
        result = await process_employee_records(records)
        return web.json_response(result)
    except Exception as e:
        logger.error(f"Error in employee data handler: {str(e)}\n{traceback.format_exc()}")
        return web.json_response({
            "success": False,
            "error": f"Server Error: {str(e)}",
            "success_count": 0,
            "error_count": 1
        }, status=500)


async def process_employee_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate and store employee records in the database."""
    employees = []
    validation_errors = []

    logger.info(f"Processing {len(records)} employee records")

    for i, record in enumerate(records):
        try:
            # Manual validation
            if not isinstance(record, dict):
                validation_errors.append({"index": i, "error": f"Record must be a dictionary, got {type(record)}"})
                continue

            # Check for required fields with more specific error messages
            required_fields = {'Employee ID', 'Name', 'Department', 'Salary'}
            field_mapping = {
                'Employee ID': 'id',
                'Name': 'name',
                'Department': 'department',
                'Salary': 'salary'
            }

            missing_fields = required_fields - set(record.keys())
            if missing_fields:
                validation_errors.append({"index": i, "error": f"Missing required fields: {missing_fields}"})
                continue

            # Type validation with friendly error messages
            if not isinstance(record['Employee ID'], int) and not (
                    isinstance(record['Employee ID'], str) and record['Employee ID'].isdigit()):
                validation_errors.append(
                    {"index": i, "error": f"'Employee ID' must be an integer or string representation of an integer"})
                continue

            if not isinstance(record['Name'], str):
                validation_errors.append({"index": i, "error": f"'Name' must be a string"})
                continue

            if not isinstance(record['Department'], str):
                validation_errors.append({"index": i, "error": f"'Department' must be a string"})
                continue

            if not isinstance(record['Salary'], (int, float)) and not (
                    isinstance(record['Salary'], str) and record['Salary'].replace('.', '', 1).isdigit()):
                validation_errors.append(
                    {"index": i, "error": f"'Salary' must be a number or string representation of a number"})
                continue

            # Convert types if needed
            id_value = int(record['Employee ID']) if isinstance(record['Employee ID'], str) else record['Employee ID']
            salary_value = float(record['Salary']) if isinstance(record['Salary'], str) else record['Salary']

            # Create Employee object with mapped fields
            employee = Employee(
                id=id_value,
                name=record['Name'],
                department=record['Department'],
                salary=salary_value
            )
            employees.append(employee)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Validation error for record {i + 1}: {error_msg}")
            validation_errors.append({"index": i, "error": error_msg})

    if not employees:
        logger.warning("No valid employee records found")
        return {
            "success": False,
            "error": "No valid employee records found",
            "validation_errors": validation_errors,
            "success_count": 0,
            "error_count": len(records)
        }

    try:
        logger.info(f"Inserting {len(employees)} valid employee records into database")
        db_result = await db.insert_employees(employees)

        success_count, error_count = db_result
        logger.info(f"Database insert results: {success_count} success, {error_count} errors")

        return {
            "success": True,
            "success_count": success_count,
            "error_count": error_count,
            "validation_errors": validation_errors,
            "message": f"Processed {len(records)} records. Inserted {success_count} successfully."
        }
    except Exception as db_error:
        logger.error(f"Database operation failed: {str(db_error)}\n{traceback.format_exc()}")
        return {
            "success": False,
            "error": f"Database error: {str(db_error)}",
            "validation_errors": validation_errors,
            "success_count": 0,
            "error_count": len(records)
        }


async def create_app() -> web.Application:
    """Create and configure the web application."""
    app = web.Application()

    # Add routes
    app.router.add_post("/api/auth", authenticate)
    app.router.add_post("/api/employees", create_employees)  # API endpoint with authentication

    # Configure the database
    try:
        logger.info("Initializing database")
        await db.create_pool()
    except Exception as e:
        logger.error(f"Error during database initialization: {str(e)}\n{traceback.format_exc()}")

    # Add cleanup logic
    async def cleanup(app: web.Application):
        try:
            logger.info("Closing database connections...")
            await db.close()
            logger.info("Database connections closed successfully.")
        except Exception as e:
            logger.error(f"Error during database cleanup: {str(e)}\n{traceback.format_exc()}")

    app.on_cleanup.append(cleanup)
    return app


def main() -> None:
    """Main entry point for the server."""
    try:
        logger.info("Starting server initialization")
        parser = argparse.ArgumentParser(description="Employee Record Server")
        parser.add_argument("--host", default="127.0.0.1", help="Server host address")
        parser.add_argument("--port", type=int, default=8000, help="Server port")
        parser.add_argument("--log-level", choices=["debug", "info", "warning", "error"], default="debug",
                            help="Set log level")
        args = parser.parse_args()

        # Configure logging level again based on args
        logging.basicConfig(level=getattr(logging, args.log_level.upper()))

        logger.info(f"Starting server at {args.host}:{args.port}")

        # Start the server
        logger.info("Creating application")
        app = asyncio.run(create_app())
        logger.info("Starting web server")
        web.run_app(app, host=args.host, port=args.port)
    except Exception as e:
        logger.critical(f"Server startup failed: {str(e)}\n{traceback.format_exc()}")
        raise


if __name__ == "__main__":
    logger.info("Script execution started")
    main()