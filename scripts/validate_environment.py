"""Environment and configuration validation script for CampusPulse."""

import os
import sys
import subprocess
from pathlib import Path

# Add backend directory to sys.path so app modules can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))


def check_python_version() -> bool:
    print(f"[*] Python Version: {sys.version.split()[0]}", end=" ")
    if sys.version_info >= (3, 11):
        print("[OK]")
        return True
    print("[FAIL] (Requires Python 3.11+)")
    return False


def check_node_version() -> bool:
    try:
        result = subprocess.run(["node", "-v"], capture_output=True, text=True, check=True)
        version = result.stdout.strip()
        print(f"[*] Node.js Version: {version} [OK]")
        return True
    except Exception as exc:
        print(f"[*] Node.js Check Failed: {exc} [FAIL]")
        return False


def check_master_spec() -> bool:
    spec_path = PROJECT_ROOT / "docs" / "CAMPUSPULSE_MASTER_SPEC.md"
    if spec_path.exists() and spec_path.stat().st_size > 1000:
        print(f"[*] Master Spec found at: docs/CAMPUSPULSE_MASTER_SPEC.md ({spec_path.stat().st_size} bytes) [OK]")
        return True
    print("[*] Master Spec missing from docs/CAMPUSPULSE_MASTER_SPEC.md [FAIL]")
    return False


def check_backend_imports() -> bool:
    try:
        from app.main import app
        from app.core.config import get_settings
        from app.core.database import check_database_connection
        settings = get_settings()
        print(f"[*] Backend Application initialized successfully: {settings.APP_NAME} ({settings.APP_ENV}) [OK]")

        db_status = check_database_connection()
        print(f"[*] Database Status: {db_status['dialect']} - Connected: {db_status['connected']} ({db_status['message']})")
        return True
    except Exception as exc:
        print(f"[*] Backend Import Failed: {exc} [FAIL]")
        return False


def main() -> int:
    print("=" * 60)
    print("CampusPulse — Environment & Readiness Verification")
    print("=" * 60)

    checks = [
        check_python_version(),
        check_node_version(),
        check_master_spec(),
        check_backend_imports(),
    ]

    all_passed = all(checks)
    print("=" * 60)
    if all_passed:
        print("RESULT: All critical environment checks PASSED.")
        return 0
    else:
        print("RESULT: Some environment checks FAILED.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
