"""Reference-layer download helpers for optional map context."""

from __future__ import annotations

import zipfile
from pathlib import Path

import requests


def download_file(url: str, output_path: str | Path, overwrite: bool = False, timeout_seconds: int = 120) -> Path:
    """Download a reference file such as a zipped shapefile or GeoPackage."""
    output = Path(output_path)
    if output.exists() and not overwrite:
        return output

    output.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=timeout_seconds) as response:
        response.raise_for_status()
        with output.open("wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)
    return output


def extract_zip(zip_path: str | Path, output_dir: str | Path, overwrite: bool = False) -> list[Path]:
    """Extract a zipped reference layer and return the extracted file paths."""
    zip_path = Path(zip_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    extracted: list[Path] = []
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            target = output / member.filename
            resolved = target.resolve()
            if not resolved.is_relative_to(output.resolve()):
                raise ValueError(f"Unsafe zip member path: {member.filename}")
            if target.exists() and not overwrite:
                extracted.append(target)
                continue
            archive.extract(member, output)
            extracted.append(target)
    return extracted
