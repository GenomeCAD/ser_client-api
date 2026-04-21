"""
HL7v2 utility functions
"""

import hashlib
from pathlib import Path

_SKIP_EXTENSIONS = {".sha256", ".hl7", ".hl7.sha256", ".hl7.ok", ".hl7.ack"}


def generate_sidecars(directory: Path) -> int:
    """Generate .sha256 sidecar files for all data files in a directory tree.

    For each data file found:
    - If the file and its sidecar both already exist, skip (avoid recomputation).
    - If the file exists but no sidecar exists, compute and write the sidecar.

    Skips .sha256, .hl7, and related non-data files to avoid creating
    sidecars of sidecars or sidecars of control files.

    :param directory: Root directory to scan recursively
    :type directory: Path
    :return: Number of sidecar files written
    :rtype: int
    """
    written = 0

    for filepath in sorted(directory.rglob("*")):
        if not filepath.is_file():
            continue

        if any(filepath.name.endswith(ext) for ext in _SKIP_EXTENSIONS):
            continue

        sidecar = filepath.parent / (filepath.name + ".sha256")
        if sidecar.exists():
            continue

        digest = hashlib.sha256(filepath.read_bytes()).hexdigest()
        sidecar.write_text(f"{digest}  {filepath.name}\n", encoding="utf-8")
        written += 1

    return written
