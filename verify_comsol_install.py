#!/usr/bin/env python3
"""Verify COMSOL installation and optional mph startup."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


def is_windows() -> bool:
    return os.name == "nt"


def candidate_executables(multiphysics_root: Path | None) -> list[Path]:
    candidates: list[Path] = []

    explicit = os.getenv("COMSOL_EXECUTABLE")
    if explicit:
        candidates.append(Path(explicit))

    if multiphysics_root:
        if is_windows():
            candidates.append(multiphysics_root / "bin" / "win64" / "comsol.exe")
        else:
            candidates.append(multiphysics_root / "bin" / "comsol")

    on_path = shutil.which("comsol")
    if on_path:
        candidates.append(Path(on_path))

    # Preserve order and drop duplicates.
    unique: list[Path] = []
    seen = set()
    for item in candidates:
        normalized = str(item)
        if normalized not in seen:
            seen.add(normalized)
            unique.append(item)
    return unique


def status(label: str, ok: bool, value: str) -> None:
    marker = "OK" if ok else "FAIL"
    print(f"[{marker}] {label}: {value}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-mph-start",
        action="store_true",
        help="Start COMSOL through mph after static checks.",
    )
    args = parser.parse_args()

    comsol_root_raw = os.getenv("COMSOL_ROOT")
    comsol_root = Path(comsol_root_raw) if comsol_root_raw else None

    multiphysics_raw = os.getenv("COMSOL_MULTIPHYSICS_ROOT")
    multiphysics_root = Path(multiphysics_raw) if multiphysics_raw else None
    if multiphysics_root is None and comsol_root is not None:
        multiphysics_root = comsol_root / "Multiphysics"

    license_value = os.getenv("LMCOMSOL_LICENSE_FILE") or os.getenv("LM_LICENSE_FILE")
    comsol_version = os.getenv("COMSOL_VERSION", "6.2")
    comsol_cores = int(os.getenv("COMSOL_CORES", "1"))

    print("=" * 70)
    print("COMSOL Installation Verification")
    print("=" * 70)

    status("COMSOL_ROOT set", bool(comsol_root_raw), comsol_root_raw or "<unset>")
    status(
        "COMSOL_MULTIPHYSICS_ROOT",
        multiphysics_root is not None,
        str(multiphysics_root) if multiphysics_root else "<unset>",
    )
    status("License variable", bool(license_value), license_value or "<unset>")
    status("COMSOL_VERSION", bool(comsol_version), comsol_version)
    status("COMSOL_CORES", comsol_cores > 0, str(comsol_cores))

    candidates = candidate_executables(multiphysics_root)
    resolved = next((path for path in candidates if path.exists()), None)
    status(
        "COMSOL executable",
        resolved is not None,
        str(resolved) if resolved else "not found from COMSOL_EXECUTABLE, COMSOL_ROOT, or PATH",
    )

    failures = []
    if not comsol_root_raw:
        failures.append("COMSOL_ROOT is not set.")
    if resolved is None:
        failures.append("COMSOL executable was not found.")
    if not license_value:
        failures.append("LMCOMSOL_LICENSE_FILE or LM_LICENSE_FILE is not set.")

    if args.check_mph_start:
        print("\nChecking mph startup...")
        try:
            import mph  # pylint: disable=import-outside-toplevel

            client = mph.start(cores=comsol_cores, version=comsol_version)
            try:
                client.clear()
            finally:
                try:
                    mph.stop()
                except Exception:
                    pass
            status("mph.start()", True, "COMSOL session started and cleaned up")
        except Exception as exc:
            failures.append(f"mph startup failed: {exc}")
            status("mph.start()", False, str(exc))
    else:
        print("\nSkipping mph startup test. Use --check-mph-start to run it.")

    if failures:
        print("\nVerification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nVerification passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
