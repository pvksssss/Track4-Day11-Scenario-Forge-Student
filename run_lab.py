"""Run the unchanged lab pipeline with an alphanumeric student ID from REPORT.md.

Usage: python run_lab.py all
The official LAB11_MSSV override supports alphanumeric IDs, while run_all.py's
report parser only accepts digits. Preserve the complete ID and its seeds.
"""
from pathlib import Path
import os
import re
import runpy


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    if not os.environ.get("LAB11_MSSV"):
        first = next(line for line in (root / "REPORT.md").read_text(encoding="utf-8").splitlines() if line.strip())
        match = re.fullmatch(r"\s*MSSV:\s*([A-Za-z0-9]{6,12})\s*", first)
        if not match:
            raise SystemExit("Write the full student ID on the first line of REPORT.md.")
        os.environ["LAB11_MSSV"] = match.group(1)
    runpy.run_path(str(root / "run_all.py"), run_name="__main__")
