import time
import logging
import functools
from typing import Callable, Dict, List, Any, TypeVar, Awaitable
import jwt
from datetime import datetime

from server.config import JWT_SECRET, JWT_ALGORITHM

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="server.log"
)
logger = logging.getLogger(__name__)

# Type hints
T = TypeVar("T")
AsyncFunc = Callable[..., Awaitable[T]]


def log_execution_time(func: Callable) -> Callable:
    """Log execution time of a synchronous function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.info(f"Function '{func.__name__}' executed in {end_time - start_time:.4f} seconds.")
        return result
    return wrapper


def async_log_execution_time(func: AsyncFunc) -> AsyncFunc:
    """Log execution time of an asynchronous function."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        logger.info(f"Async function '{func.__name__}' executed in {end_time - start_time:.4f} seconds.")
        return result
    return wrapper


def log_request(func: AsyncFunc) -> AsyncFunc:
    """Log API request details."""
    @functools.wraps(func)
    async def wrapper(request, *args, **kwargs):
        logger.info(f"Request received: {request.method} {request.path} from {request.remote}")
        return await func(request, *args, **kwargs)
    return wrapper


def validate_jwt(func: AsyncFunc) -> AsyncFunc:
    """Validate JWT token in the request headers."""
    @functools.wraps(func)
    async def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            logger.warning("Missing or invalid Authorization token.")
            return web.json_response({"error": "Invalid token"}, status=401)

        token = auth_header.split(" ")[1]
        try:
            jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return await func(request, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            logger.warning("Authorization token has expired.")
            return web.json_response({"error": "Invalid token"}, status=401)
        except jwt.InvalidTokenError:
            logger.warning("Invalid authorization token.")
            return web.json_response({"error": "Invalid token"}, status=401)
    return wrapper


def validate_employee_records(func: Callable) -> Callable:
    """Validate employee records before processing."""
    @functools.wraps(func)
    def wrapper(records: List[Dict[str, Any]], *args, **kwargs):
        valid_records = []
        invalid_records = []
        required_fields = [
            "employee_id", "name", "email", "department",
            "designation", "salary", "date_of_joining"
        ]

        for record in records:
            missing_fields = [field for field in required_fields if field not in record]
            if missing_fields:
                logger.warning(f"Missing fields in record: {missing_fields}.")
                invalid_records.append({"record": record, "error": f"Missing fields: {', '.join(missing_fields)}"})
                continue

            if "@" not in record.get("email", ""):
                logger.warning(f"Invalid email: {record.get('email')}.")
                invalid_records.append({"record": record, "error": "Invalid email format"})
                continue

            try:
                record["salary"] = float(record["salary"])
            except (ValueError, TypeError):
                logger.warning(f"Invalid salary: {record.get('salary')}.")
                invalid_records.append({"record": record, "error": "Invalid salary format"})
                continue

            try:
                datetime.strptime(record["date_of_joining"], "%Y-%m-%d")
            except ValueError:
                logger.warning(f"Invalid date format: {record.get('date_of_joining')}.")
                invalid_records.append({
                    "record": record, "error": "Invalid date format. Expected YYYY-MM-DD"
                })
                continue

            valid_records.append(record)

        # Proceed with only valid records
        result = func(valid_records, *args, **kwargs)
        if isinstance(result, dict):
            result.update({
                "valid_count": len(valid_records),
                "invalid_count": len(invalid_records),
                "invalid_records": invalid_records
            })
        return result
    return wrapper