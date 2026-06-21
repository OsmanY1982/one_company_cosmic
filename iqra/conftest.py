"""Pytest configuration - ensure iqra package is importable."""
import sys
import os

# Add project root to path so `core`, `agent`, `tools`, etc. are importable
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
