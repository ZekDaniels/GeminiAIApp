import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import MagicMock
from app.services.integration_service import PDFService

client = TestClient(app)


@pytest.fixture
def mock_integration_service(mocker):
    """
    Mock PDFService methods for testing.
    """
    mock_service = MagicMock(spec=PDFService)
    mocker.patch("app.routes.pdf_route.integration_service", mock_service)
    return mock_service


def test_upload_pdf(mock_integration_service):
    """
    Test uploading a PDF document.
    """
    mock_integration_service.process_integration.return_value = 1

    file_content = b"Sample PDF content"
    files = {"file": ("test.pdf", file_content, "application/pdf")}

    response = client.post("/v1/pdf/", files=files)

    assert response.status_code == 200
    assert response.json() == {"integration_id": 1, "filename": "test.pdf"}
    mock_integration_service.process_integration.assert_called_once()


def test_delete_integration(mock_integration_service):
    """
    Test deleting a PDF document.
    """
    response = client.delete("/v1/pdf/1")
    assert response.status_code == 204
    mock_integration_service.delete_integration.assert_called_once_with(1, mock_integration_service.delete_integration.call_args[0][1])


def test_list_integrations(mock_integration_service):
    """
    Test listing all uploaded PDFs.
    """
    mock_integration_service.list_integrations.return_value = [
        {"id": 1, "filename": "test.pdf", "content": "Sample content"}
    ]

    response = client.get("/v1/pdf/")
    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "filename": "test.pdf", "content": "Sample content"}
    ]
    mock_integration_service.list_integrations.assert_called_once()


def test_get_integration_by_id(mock_integration_service):
    """
    Test retrieving a PDF by ID.
    """
    mock_integration_service.get_integration_by_id.return_value = {
        "id": 1,
        "filename": "test.pdf",
        "content": "Sample content",
    }

    response = client.get("/v1/pdf/1")
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "filename": "test.pdf",
        "content": "Sample content",
    }
    mock_integration_service.get_integration_by_id.assert_called_once_with(
        1, mock_integration_service.get_integration_by_id.call_args[0][1]
    )
