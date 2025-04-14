import functools
import time
import logging
import asyncio
from typing import List, Dict, Any, Callable
from jwt import decode, exceptions
from client.config import JWT_SECRET, JWT_ALGORITHM

logger = logging.getLogger('client')


def log_request(func):
    """Decorator to log HTTP requests"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"Making request to {kwargs.get('url', 'unknown URL')}")
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        logger.debug(f"Request completed in {elapsed:.2f}s")
        return result
    return wrapper


def async_log_execution_time(func):
    """Decorator to log execution time for async functions"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start_time
        logger.debug(f"{func.__name__} executed in {elapsed:.2f}s")
        return result
    return wrapper


def validate_jwt(func: Callable) -> Callable:
    """Decorator to validate a JWT token and pass the payload to the wrapped function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        token = kwargs.get('token') or (args[0] if args else None)

        if token is None:
            logger.error("No token provided for validation.")
            raise ValueError("Token is required for JWT validation.")

        try:
            if isinstance(token, str):
                token = token.encode("utf-8")

            payload = decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            logger.debug(f"Decoded JWT Payload: {payload}")
            kwargs['jwt_payload'] = payload
        except exceptions.DecodeError as e:
            logger.error(f"JWT decoding error: {str(e)}")
            raise ValueError(f"Invalid token: {str(e)}")
        except exceptions.PyJWTError as e:
            logger.error(f"JWT validation error: {str(e)}")
            raise ValueError(f"JWT processing error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in JWT validation: {str(e)}")
            raise ValueError(f"JWT validation failed: {str(e)}")

        return func(*args, **kwargs)
    return wrapper


def validate_employee_records(func: Callable) -> Callable:
    """Decorator to validate employee records before sending."""
    @functools.wraps(func)
    def wrapper(records: List[Dict[str, Any]], *args, **kwargs):
        if not records:
            logger.warning("No employee records provided")
            return []

        valid_records = []
        for record in records:
            try:
                required_keys = ['employee_id', 'name', 'department']
                for key in required_keys:
                    if key not in record or not record[key]:
                        raise ValueError(f"Missing or invalid field: {key}")

                valid_records.append(record)
            except ValueError as e:
                logger.warning(f"Skipping invalid record {record}: {str(e)}")

        if len(valid_records) < len(records):
            logger.info(f"Filtered out {len(records) - len(valid_records)} invalid records")
        return func(valid_records, *args, **kwargs)
    return wrapper