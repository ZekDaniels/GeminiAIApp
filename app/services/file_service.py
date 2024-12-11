import os
import aiofiles
import uuid
import logging

logger = logging.getLogger("app")


class FileHandler:
    """
    Handles file-related operations such as saving, deleting, backing up,
    and restoring files.
    """

    def __init__(self, upload_dir: str):
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

    def generate_unique_filename(self, original_filename: str) -> str:
        """Generate a unique filename using UUID."""
        unique_id = uuid.uuid4().hex
        file_extension = os.path.splitext(original_filename)[1]
        return f"{unique_id}{file_extension}"

    async def save_file(self, file) -> str:
        """Save an uploaded file to disk."""
        unique_filename = self.generate_unique_filename(file.filename)
        file_path = os.path.normpath(os.path.join(self.upload_dir, unique_filename))  # Normalize path
        async with aiofiles.open(file_path, "wb") as buffer:
            await buffer.write(await file.read())
        logger.info("File saved: %s", file_path)
        return unique_filename

    def backup_file(self, filename: str) -> str:
        """Backup an existing file."""
        original_path = os.path.join(self.upload_dir, filename)
        backup_path = f"{original_path}.bak"
        if not os.path.exists(original_path):
            logger.warning("File not found for backup: %s", original_path)
            return backup_path
        os.rename(original_path, backup_path)
        logger.info("Backup created: %s", backup_path)
        return backup_path

    def restore_backup(self, backup_path: str, original_filename: str):
        """Restore a file from its backup."""
        original_path = os.path.join(self.upload_dir, original_filename)
        
        # Ensure the backup file exists before restoring
        if not os.path.exists(backup_path):
            logger.warning("Backup file not found for restoration: %s", backup_path)
            return

        # If the target file already exists, delete it first
        if os.path.exists(original_path):
            logger.warning("Target file exists, removing it before restoring backup: %s", original_path)
            os.remove(original_path)

        # Rename the backup file to the original path
        os.rename(backup_path, original_path)
        logger.info("Backup restored: %s", original_path)



    def delete_file(self, filename: str):
        """Delete a file from disk."""
        file_path = os.path.join(self.upload_dir, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info("File deleted: %s", file_path)
        else:
            logger.warning("File not found for deletion: %s", file_path)
