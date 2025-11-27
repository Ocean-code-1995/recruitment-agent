"""Database CLI utilities."""

import sys
import os

# Add project root to sys.path for all db scripts
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

