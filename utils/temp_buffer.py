import os
import shutil
from pathlib import Path

from core.constants import INPUT_PATH_NAME, OUTPUT_PATH_NAME
from core.logger import setup_logger

logger = setup_logger(name=__name__)


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


def get_user_temp_paths(user_id: int | str) -> tuple[Path, Path]:
    """Создает и возвращает пути к временным папкам пользователя."""
    base_dir = Path("temp") / str(user_id)
    
    path_in = base_dir / "IN"
    path_out = base_dir / "OUT"

    # mkdir создает сразу всю цепочку директорий с безопасными правами
    path_in.mkdir(parents=True, exist_ok=True)
    path_out.mkdir(parents=True, exist_ok=True)

    return path_in, path_out


def clear_folder(folder_path: str | Path) -> None:
    """Удаляет все файлы и подпапки внутри указанной директории."""
    path = Path(folder_path)
    if not path.exists():
        return

    for item in path.iterdir():
        try:
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        except Exception as e:
            logger.error(f"Ошибка при удалении {item}: {e}")


def remove_user_temp_dir(user_id: int | str) -> None:
    """Полностью удаляет всю временную папку пользователя."""
    user_dir = Path("temp") / str(user_id)
    if user_dir.exists():
        try:
            shutil.rmtree(user_dir)
            logger.debug(f"Временная директория {user_dir} успешно удалена")
        except Exception as e:
            logger.error(f"Ошибка при удалении директории пользователя {user_dir}: {e}")
