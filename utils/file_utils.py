"""File helpers for dataset and encrypted report storage."""

from __future__ import annotations

import json
from pathlib import Path


REQUIRED_WRAPPER_KEYS = {
    "app",
    "report_id",
    "timestamp",
    "nonce",
    "ciphertext",
    "stored_integrity_hash",
    "educational_notice",
    "encryption_scheme",
}


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def resolve_dataset_path(base_dir: Path) -> Path:
    data_path = base_dir / "data" / "StudentPerformanceFactors.csv"
    if data_path.exists():
        return data_path
    return base_dir / "StudentPerformanceFactors.csv"


def save_encrypted_wrapper(records_dir: Path, wrapper: dict) -> Path:
    ensure_directory(records_dir)
    file_path = records_dir / f"{wrapper['report_id']}.json"
    file_path.write_text(json.dumps(wrapper, indent=2, ensure_ascii=True), encoding="utf-8")
    return file_path


def load_encrypted_wrapper(file_path: Path) -> dict:
    try:
        raw_text = file_path.read_text(encoding="utf-8")
        payload = json.loads(raw_text)
    except OSError as error:
        raise ValueError("The selected report file could not be opened.") from error
    except json.JSONDecodeError as error:
        raise ValueError("The selected report file is not valid JSON.") from error

    missing_keys = sorted(REQUIRED_WRAPPER_KEYS - payload.keys())
    if missing_keys:
        raise ValueError(f"The saved report is missing required fields: {', '.join(missing_keys)}")

    return payload