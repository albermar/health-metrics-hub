from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import shutil

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
        Move file_id to base_path / target_dir / filename (unique if collision)
        Returns the new file path as string
        """
        source = Path(file_id)

        if not source.exists():
            raise FileNotFoundError(f"File not found: {file_id}")

        destination_dir = self._base_path / target_dir
        destination_dir.mkdir(parents=True, exist_ok=True)

        destination = destination_dir / source.name

        # If destination already exists, create a unique name (versioned)
        if destination.exists():
            destination = self._unique_destination(destination_dir, source)

        # Use shutil.move for robustness across devices/filesystems
        shutil.move(str(source), str(destination))
        return str(destination)

    def _unique_destination(self, destination_dir: Path, source: Path) -> Path:
        stem = source.stem
        suffix = source.suffix

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        candidate = destination_dir / f"{stem}__{ts}{suffix}"
        if not candidate.exists():
            return candidate

        # Ultra edge-case: same second, multiple moves
        i = 1
        while True:
            candidate = destination_dir / f"{stem}__{ts}__{i}{suffix}"
            if not candidate.exists():
                return candidate
            i += 1
