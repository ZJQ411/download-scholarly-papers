#!/usr/bin/env python3
"""Validate, deduplicate, organize, and optionally zip scholarly PDF files.

This script deliberately accepts no credentials and performs no network access.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import shutil
import sys
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from pypdf import PdfReader
except ModuleNotFoundError as exc:  # pragma: no cover - environment dependent
    raise SystemExit(
        "pypdf is required. Use the Codex bundled Python runtime or install pypdf."
    ) from exc


INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


@dataclass
class PaperResult:
    source_file: str
    output_file: str
    status: str
    bytes: int
    pages: int
    encrypted: bool | None
    sha256: str
    title: str
    first_page_text_chars: int
    error: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_filename(name: str) -> str:
    cleaned = INVALID_FILENAME_CHARS.sub("_", name).strip().rstrip(". ")
    return cleaned or "paper.pdf"


def verify_pdf(path: Path) -> PaperResult:
    result = PaperResult(
        source_file=str(path),
        output_file="",
        status="invalid",
        bytes=path.stat().st_size,
        pages=0,
        encrypted=None,
        sha256="",
        title="",
        first_page_text_chars=0,
        error="",
    )
    try:
        with path.open("rb") as stream:
            if stream.read(5) != b"%PDF-":
                raise ValueError("missing PDF signature")
        result.sha256 = sha256_file(path)
        reader = PdfReader(str(path), strict=False)
        result.encrypted = bool(reader.is_encrypted)
        if result.encrypted:
            raise ValueError("encrypted PDF")
        result.pages = len(reader.pages)
        if result.pages < 1:
            raise ValueError("PDF has no pages")
        metadata = reader.metadata
        result.title = str(metadata.title or "") if metadata else ""
        first_page_text = reader.pages[0].extract_text() or ""
        result.first_page_text_chars = len(first_page_text)
        result.status = "valid"
    except Exception as exc:  # pypdf exposes several version-specific errors
        result.error = f"{type(exc).__name__}: {exc}"
    return result


def unique_destination(output_dir: Path, filename: str, digest: str) -> Path:
    candidate = output_dir / safe_filename(filename)
    if not candidate.exists():
        return candidate
    if sha256_file(candidate) == digest:
        return candidate
    return candidate.with_name(f"{candidate.stem}_{digest[:8]}{candidate.suffix}")


def write_manifest(path: Path, rows: list[PaperResult]) -> None:
    fields = list(PaperResult.__dataclass_fields__)
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)


def create_zip(zip_path: Path, files: list[Path], manifest: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files, key=lambda item: item.name.lower()):
            archive.write(path, arcname=path.name)
        archive.write(manifest, arcname=manifest.name)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--zip", dest="zip_path", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--recursive", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_dir = args.source_dir.resolve()
    if not source_dir.is_dir():
        print(f"Source directory does not exist: {source_dir}", file=sys.stderr)
        return 2

    output_dir = args.output_dir.resolve() if args.output_dir else None
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    pattern = "**/*.pdf" if args.recursive else "*.pdf"
    candidates = []
    for path in source_dir.glob(pattern):
        resolved = path.resolve()
        if output_dir and output_dir in resolved.parents:
            continue
        if resolved.is_file():
            candidates.append(resolved)
    candidates.sort(key=lambda item: str(item).lower())

    rows: list[PaperResult] = []
    seen_hashes: dict[str, str] = {}
    organized_files: list[Path] = []

    for path in candidates:
        row = verify_pdf(path)
        if row.status == "valid" and row.sha256 in seen_hashes:
            row.status = "duplicate"
            row.output_file = seen_hashes[row.sha256]
        elif row.status == "valid":
            if output_dir:
                destination = unique_destination(output_dir, path.name, row.sha256)
                if not destination.exists():
                    shutil.copy2(path, destination)
                row.output_file = str(destination)
                organized_files.append(destination)
            else:
                row.output_file = str(path)
                organized_files.append(path)
            seen_hashes[row.sha256] = row.output_file
        rows.append(row)

    manifest = (
        args.manifest.resolve()
        if args.manifest
        else (output_dir or source_dir) / "paper_validation_manifest.csv"
    )
    manifest.parent.mkdir(parents=True, exist_ok=True)
    write_manifest(manifest, rows)

    if args.zip_path:
        create_zip(args.zip_path.resolve(), organized_files, manifest)

    valid = sum(row.status == "valid" for row in rows)
    duplicates = sum(row.status == "duplicate" for row in rows)
    invalid = sum(row.status == "invalid" for row in rows)
    print(
        f"scanned={len(rows)} valid={valid} duplicates={duplicates} "
        f"invalid={invalid} manifest={manifest}"
    )
    return 1 if invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())
