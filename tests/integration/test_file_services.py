import os
import pytest
from unittest.mock import AsyncMock, patch
from app.services.file_service import FileHandler


@pytest.fixture
def file_handler():
    return FileHandler(upload_dir="test_uploads")


def test_generate_unique_filename(file_handler):
    filename = "example.pdf"
    unique_filename = file_handler.generate_unique_filename(filename)
    assert unique_filename.endswith(".pdf")
    assert len(unique_filename.split(".")[0]) == 32  # UUID length


@patch("aiofiles.open")
@pytest.mark.asyncio
async def test_save_file(mock_aiofiles_open, file_handler):
    # Mock file object
    mock_file = AsyncMock()
    mock_file.filename = "test.pdf"
    mock_file.read.return_value = b"Test content"

    # Mock aiofiles.open to simulate async context manager behavior
    mock_file_handle = AsyncMock()
    mock_aiofiles_open.return_value.__aenter__.return_value = mock_file_handle

    # Call the method under test
    unique_filename = await file_handler.save_file(mock_file)

    # Normalize expected path for cross-platform compatibility
    expected_path = os.path.normpath(f"test_uploads/{unique_filename}")

    # Assertions
    assert unique_filename.endswith(".pdf")
    assert len(unique_filename.split(".")[0]) == 32  # UUID length
    mock_aiofiles_open.assert_called_once_with(expected_path, "wb")
    mock_file_handle.write.assert_called_once_with(b"Test content")



def test_backup_file(file_handler):
    with patch("os.rename") as mock_rename:
        backup_path = file_handler.backup_file("test.pdf")
        assert backup_path.endswith(".bak")
        mock_rename.assert_called_once()


def test_restore_backup(file_handler):
    with patch("os.rename") as mock_rename:
        file_handler.restore_backup("test.pdf.bak", "test.pdf")
        mock_rename.assert_called_once()


def test_delete_file(file_handler):
    with patch("os.path.exists", return_value=True), patch("os.remove") as mock_remove:
        file_handler.delete_file("test.pdf")
        mock_remove.assert_called_once()

    with patch("os.path.exists", return_value=False):
        file_handler.delete_file("test.pdf")  # Should not call os.remove
