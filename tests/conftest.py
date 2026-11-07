"""Make repository-root modules importable during pytest collection.

GitHub Actions invokes pytest from the repository root, but pytest's import
mode can place the tests directory ahead of the project root. Explicitly add
the project root so tests behave consistently in local and CI environments.
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
project_root = str(PROJECT_ROOT)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
