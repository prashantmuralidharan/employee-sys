from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
from pydantic import BaseModel, ValidationError, Field

@dataclass
class Employee:
    employee_id: str
    name: str
    department: str
    role: str
    salary: float
    hire_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    active: bool = True
    contact_info: Dict[str, str] = field(default_factory=dict)
    skills: List[str] = field(default_factory=list)
    manager_id: Optional[str] = None
    performance_rating: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert Employee object to dictionary"""
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "department": self.department,
            "role": self.role,
            "salary": self.salary,
            "hire_date": self.hire_date,
            "active": self.active,
            "contact_info": self.contact_info,
            "skills": self.skills,
            "manager_id": self.manager_id,
            "performance_rating": self.performance_rating
        }

    def to_json(self) -> str:
        """Convert Employee object to JSON string"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Employee':
        """Create Employee object from dictionary"""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'Employee':
        """Create Employee object from JSON string"""
        return cls.from_dict(json.loads(json_str))


class EmployeeSchema(BaseModel):
    """Schema for validating Employee data"""
    employee_id: str
    name: str
    department: str
    role: str
    salary: float = Field(..., ge=0)  # Enforces salary to be non-negative
    hire_date: Optional[str] = None  # ISO 8601 format, validated automatically
    active: bool = True
    contact_info: Dict[str, str] = Field(default_factory=dict)
    skills: List[str] = Field(default_factory=list)
    manager_id: Optional[str] = None
    performance_rating: Optional[float] = Field(None, ge=0, le=5)  # Enforces rating range (0-5)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.strftime("%Y-%m-%d")
        }

    def to_employee(self) -> Employee:
        """Convert schema to Employee object"""
        return Employee(
            employee_id=self.employee_id,
            name=self.name,
            department=self.department,
            role=self.role,
            salary=self.salary,
            hire_date=self.hire_date or datetime.now().strftime("%Y-%m-%d"),
            active=self.active,
            contact_info=self.contact_info,
            skills=self.skills,
            manager_id=self.manager_id,
            performance_rating=self.performance_rating
        )
