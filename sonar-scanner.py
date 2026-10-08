# Aufruf:   python sonar-scanner.py

"""Python-Script, um den Scanner für SonarQube aufzurufen."""

import subprocess  # ruff: ignore[suspicious-subprocess-import]
from pathlib import Path
from sysconfig import get_platform

betriebssystem = get_platform()
base_path = (
    (Path("C:\\") / "Zimmermann")
    if betriebssystem in {"win-amd64", "win-arm64", "win32"}
    else Path("Zimmermann")
)
script = Path(base_path) / "sonar-scanner" / "bin" / "sonar-scanner"

subprocess.run(f"{script} -X", shell=True)  # ruff: ignore[subprocess-run-without-check, subprocess-popen-with-shell-equals-true]
