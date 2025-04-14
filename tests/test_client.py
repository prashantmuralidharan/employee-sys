import pytest
import asyncio
import aiohttp
from client.client import EmployeeClient
from client.utils import read_csv_file, chunk_records
from unittest.mock import patch, MagicMock


class TestClientUtils:
    """Test client utility functions."""

    def test_read_csv_file(self, sample_csv_file):
        """Test reading employee records from a CSV file."""
        records = read_csv_file(sample_csv_file)

        assert len(records) == 100
        assert "employee_id" in records[0]
        assert "name" in records[0]
        assert "email" in records[0]

    def test_chunk_records(self):
        """Test splitting records into batches."""
        # Create test records
        records = [{"id": i} for i in range(100)]

        # Split into batches of 25
        batches = chunk_records(records, 25)

        assert len(batches) == 4
        assert len(batches[0]) == 25
        assert len(batches[3]) == 25

        # Test with non-divisible batch size
        batches = chunk_records(records, 30)

        assert len(batches) == 4
        assert len(batches[0]) == 30
        assert len(batches[3]) == 10


@pytest.mark.asyncio
class TestEmployeeClient:
    """Test the EmployeeClient class."""

    async def test_send_batch(self, mock_client_session):
        """Test sending a batch of employee records."""
        client = EmployeeClient(server_url="http://test-server.com/api")

        # Create test batch
        batch = [{"employee_id": f"EMP{i}"} for i in range(10)]

        # Send batch
        with patch("aiohttp.ClientSession", return_value=mock_client_session):
            result = await client.send_batch(mock_client_session, batch)

        # Verify the batch was sent correctly
        mock_client_session.post.assert_called_once()
        assert result["success_count"] == 10

    async def test_process_file(self, sample_csv_file, mock_client_session):
        """Test processing a CSV file."""
        client = EmployeeClient(server_url="http://test-server.com/api")

        # Mock aiohttp.ClientSession to return our mock session
        with patch("aiohttp.ClientSession", return_value=mock_client_session):
            with patch("client.client.read_csv_file") as mock_read_csv:
                # Setup mock data
                mock_records = [{"employee_id": f"EMP{i}"} for i in range(100)]
                mock_read_csv.return_value = mock_records

                # Process file
                result = await client.process_file(sample_csv_file, batch_size=20)

        # Verify results
        assert result["total_records"] == 100
        assert result["success_count"] > 0

        # Verify the correct number of batches were sent
        assert mock_client_session.post.call_count == 5  # 100 records in batches of 20 = 5 batches

    async def test_retry_on_error(self, mock_client_session):
        """Test retry logic for failed requests."""
        client = EmployeeClient(server_url="http://test-server.com/api")

        # Create test batch
        batch = [{"employee_id": f"EMP{i}"} for i in range(10)]

        # Configure the mock to fail on first attempt, succeed on second
        side_effects = [
            aiohttp.ClientError("Connection error"),  # First call fails
            MagicMock(  # Second call succeeds
                status=200,
                json=MagicMock(return_value={"success_count": 10, "error_count": 0})
            )
        ]

        mock_client_session.post.side_effect = side_effects

        # Patch the backoff decorator to make it retry immediately
        with patch("client.client.backoff.on_exception", return_value=lambda f: f):
            with patch.object(client, "send_batch", side_effect=side_effects):
                # This should raise the first error
                with pytest.raises(aiohttp.ClientError):
                    await client.send_batch(mock_client_session, batch)
