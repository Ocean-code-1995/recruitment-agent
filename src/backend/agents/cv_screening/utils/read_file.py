from pathlib import Path

def read_file(path: Path) -> str:
    """Read the contents of a file and return as a string.
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()