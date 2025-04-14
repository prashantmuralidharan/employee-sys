import pytest
import json
from aiohttp import web
from server.server import create_employees, authenticate, process_employee_records
from server.models import Employee
from unittest.mock import patch, MagicMock


@pytest.mark.asyncio
class TestServerEndpoints:
    """Test server API endpoints."""

    async def test_authenticate(self, test_client):
        """Test authentication endpoint."""
        # Test with valid API key
        resp = await test_client.post(
            "/api/auth",
            json={"api_key": "your_default_api_key"}
        )

        assert resp.status == 200
        data = await resp.json()
        assert "token" in data

        # Test with invalid API key
        resp = await test_client.post(
            "/api/auth",
            json={"api_key": "invalid_key"}
        )

        assert resp.status == 401

    async def test_create_employees(self, test_client, mock_jwt_token, sample_employee_data):
        """Test endpoint for creating employee records."""
        # Test with valid data
        resp = await test_client.post(
            "/api/employees",
            headers={"Authorization": f"Bearer {mock_jwt_token}"},
            json=sample_employee_data[:10]  # Send 10 records
        )

        assert resp.status == 200
        data = await resp.json()
        assert data["success"] is True
        assert data["success_count"] == 10

        # Test with invalid data format
        resp = await test_client.post(
            "/api/employees",
            headers={"Authorization": f"Bearer {mock_jwt_token}"},
            json={"not_a_list": "this should fail"}
        )

        assert resp.status == 400

    async def test_missing_jwt(self, test_client, sample_employee_data):
        """Test API call without JWT token."""
        resp = await test_client.post(
            "/api/employees",
            json=sample_employee_data[:5]
        )

        assert resp.status == 401

    async def test_invalid_jwt(self, test_client, sample_employee_data):
        """Test API call with invalid JWT token."""
        resp = await test_client.post(
            "/api/employees",
            headers={"Authorization": "Bearer invalid.token.here"},
            json=sample_employee_data[:5]
        )

        assert resp.status == 401


@pytest.mark.asyncio
class TestEmployeeProcessing:
    """Test employee record processing."""

    async def test_process_valid_records(self, mock_db):
        """Test processing valid employee records."""
        # Create valid test records
        valid_records = [
            {
                "employee_id": "EMP001",
                "name": "Valid Employee",
                "email": "valid@example.com",
                "department": "Testing",
                "designation": "Tester",
                "salary": "75000.00",
                "date_of_joining": "2022-01-01"
            }
        ]

        # Process the records
        with patch("server.server.db", mock_db):
            result = await process_employee_records(valid_records)

        # Verify results
        assert result["success"] is True
        assert result["success_count"] == 10  # From mock db.insert_employees
        assert result["valid_count"] == 1

    async def test_process_invalid_records(self, mock_db):
        """Test processing invalid employee records."""
        # Create invalid test records
        invalid_records = [
            {
                "employee_id": "EMP002",
                "name": "Invalid Employee",
                # Missing email field
                "department": "Testing",
                "designation": "Tester",
                "salary": "75000.00",
                "date_of_joining": "2022-01-01"
            },
            {
                "employee_id": "EMP003",
                "name": "Invalid Email",
                "email": "not-an-email",  # Invalid email format
                "department": "Testing",
                "designation": "Tester",
                "salary": "75000.00",
                "date_of_joining": "2022-01-01"
            },
            {
                "employee_id": "EMP004",
                "name": "Invalid Date",
                "email": "valid@example.com",
                "department": "Testing",
                "designation": "Tester",
                "salary": "75000.00",
                "date_of_joining": "not-a-date"  # Invalid date format
            }
        ]

        # Process the records
        with patch("server.server.db", mock_db):
            result = await process_employee_records(invalid_records)

        # Verify results
        assert result["success"] is True
        assert result["invalid_count"] == 3
        assert "invalid_records" in result
        assert len(result["invalid_records"]) == 3