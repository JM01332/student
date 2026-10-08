# Aufruf:   uv run extras/dependency-check.py

"""Python-Script, um OWASP Dependency Check aufzurufen."""

import subprocess  # ruff: ignore[suspicious-subprocess-import]
from os import environ
from pathlib import Path
from sysconfig import get_platform

from dotenv import load_dotenv

load_dotenv()
nvd_api_key = environ.get("NVD_API_KEY")
if not nvd_api_key:
    print("NVD_API_KEY fehlt: in .env eintragen (siehe .env.example)")
    raise SystemExit(1)

project = "student"

base_script = "dependency-check"
betriebssystem = get_platform()
if betriebssystem in {"win-amd64", "win-arm64", "win32"}:
    base_path = Path("C:/") / "Zimmermann"
    base_script += ".bat"
else:
    base_path = Path("Zimmermann")

script = base_path / "dependency-check" / "bin" / base_script
print(f"script={script}")

data_path = base_path / "dependency-check-data"
scan_path = Path()
report_path = "."

options = " ".join([
    f"--nvdApiKey {nvd_api_key} --project {project} --scan {scan_path}",
    f"--suppression extras/suppression.xml --out {report_path} --data {data_path}",
    # Python-Analyzer sind bei Dependency Check "experimentell" und sonst deaktiviert
    "--enableExperimental",
    # dependency-check.bat --advancedHelp
    "--disableArchive",
    "--disableAssembly",
    "--disableAutoconf",
    "--disableBundleAudit",
    "--disableCarthageAnalyzer",
    "--disableCentral",
    "--disableCentralCache",
    "--disableCmake",
    "--disableCocoapodsAnalyzer",
    "--disableComposer",
    "--disableCpan",
    "--disableDart",
    "--disableGolangDep",
    "--disableGolangMod",
    "--disableJar",
    "--disableMavenInstall",
    "--disableMixAudit",
    "--disableMSBuild",
    "--disableNodeAudit",
    "--disableNodeAuditCache",
    "--disableNodeJS",
    "--disableNugetconf",
    "--disableNuspec",
    "--disableOssIndex",
    "--disablePipfile",
    "--disablePnpmAudit",
    "--disableRubygems",
    "--disableSwiftPackageManagerAnalyzer",
    "--disableSwiftPackageResolvedAnalyzer",
    "--disableYarnAudit",
])

subprocess.run(f"{script} {options}", shell=True)  # ruff: ignore[subprocess-run-without-check, subprocess-popen-with-shell-equals-true]
