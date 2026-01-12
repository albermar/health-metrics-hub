from pathlib import Path
from app.domain.interfaces import FileStorage_Interface

class DI_LocalFileStorage(FileStorage_Interface):
    def __init__(self, base_path: str):
        self._base_path = Path(base_path)

    def save_uploaded_csv(self, file_bytes: bytes, filename: str) -> str:
        self._base_path.mkdir(parents=True, exist_ok=True)
        file_path = self._base_path / filename
        file_path.write_bytes(file_bytes)
        return str(file_path)

    def move_csv_to_processed(self, file_id: str) -> str:
        return self._move_file(file_id, "processed")

    def move_csv_to_unprocessable(self, file_id: str) -> str:
        return self._move_file(file_id, "unprocessable")

    def _move_file(self, file_id: str, target_dir: str) -> str:
        """
        Move file_id to base_path / target_dir / filename
        Returns the new file path as string
        """
        source = Path(file_id)

        if not source.exists():
            raise FileNotFoundError(f"File not found: {file_id}")

        destination_dir = self._base_path / target_dir
        destination_dir.mkdir(parents=True, exist_ok=True)

        destination = destination_dir / source.name
        source.rename(destination)

        return str(destination)