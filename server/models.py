"""
Data models for employee records using dataclasses and Pydantic validation.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid

# Dataclass-based models
@dataclass
class Employee:
    """Employee record with validation."""
    employee_id: str
    name: str
    email: str
    department: str
    designation: str
    salary: float
    date_of_joining: datetime
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Employee':
        """Convert dictionary to Employee instance."""
        try:
            # Validate and convert fields
            if isinstance(data.get("date_of_joining"), str):
                data["date_of_joining"] = datetime.strptime(data["date_of_joining"], "%Y-%m-%d")
            if "salary" in data:
                data["salary"] = float(data["salary"])
        except (ValueError, TypeError) as e:
            raise ValueError(f"Error processing input data: {str(e)}")

        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert Employee instance to dictionary."""
        employee_dict = asdict(self)
        return self._convert_datetime_to_string(employee_dict)

    def to_db_dict(self) -> Dict[str, Any]:
        """Convert Employee instance to dictionary for database."""
        employee_dict = self.to_dict()

        # Format datetime fields for database
        for key in ["date_of_joining", "created_at", "updated_at"]:
            if key in employee_dict and isinstance(self.__dict__[key], datetime):
                employee_dict[key] = self.__dict__[key].strftime("%Y-%m-%d %H:%M:%S")
        return employee_dict

    @staticmethod
    def _convert_datetime_to_string(data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert datetime fields in a dictionary to ISO format strings."""
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data


# Pydantic-based schema for validation
try:
    from pydantic import BaseModel, EmailStr, Field, validator

    class EmployeeSchema(BaseModel):
        """Employee schema using Pydantic."""
        employee_id: str
        name: str
        email: EmailStr
        department: str
        designation: str
        salary: float
        date_of_joining: str

        @validator("date_of_joining")
        def validate_date(cls, v):
            """Validate date format."""
            try:
                datetime.strptime(v, "%Y-%m-%d")
                return v
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD")

        @validator("salary")
        def validate_salary(cls, v):
            """Validate salary."""
            if v < 0:
                raise ValueError("Salary cannot be negative")
            return v

        def to_employee(self) -> Employee:
            """Convert to Employee dataclass instance."""
            data = self.dict()
            data["date_of_joining"] = datetime.strptime(data["date_of_joining"], "%Y-%m-%d")
            return Employee.from_dict(data)

except ImportError:
    class EmployeeSchema:
        """Dummy schema when Pydantic is not installed."""
        def __init__(self, *args, **kwargs):
            raise ImportError("Pydantic is not installed. Install it for schema validation.")