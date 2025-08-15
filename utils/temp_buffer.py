import os
from pathlib import Path

from core.constants import INPUT_PATH_NAME, OUTPUT_PATH_NAME
from core.logger import setup_logger

logger = setup_logger(name='temp_buffer')


def create_temp_folder(user_id):
    """Create a temporary folder for the user if it doesn't exist."""
    path_in = Path(f'temp/{user_id}/{INPUT_PATH_NAME}')
    path_in.mkdir(mode=0o777, parents=True, exist_ok=True)
    path_out = Path(f'temp/{user_id}/{OUTPUT_PATH_NAME}')
    path_out.mkdir(mode=0o777, parents=True, exist_ok=True)
    path = (path_in.as_posix(), path_out.as_posix())
    return path


def delete_files_in_folder(folder_path):
    """Delete all files in the specified folder."""
    if not os.path.exists(folder_path):
        return  # Folder does not exist, nothing to delete
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
