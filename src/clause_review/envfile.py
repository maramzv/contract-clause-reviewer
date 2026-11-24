"""Load settings from a .env file, so the key and spend limit in .env are actually used.

Looks for a file named .env in the current folder, then up to two folders above it (the repository's top folder when
you run from src/). Lines look like KEY=value; blank lines and lines starting with # are skipped, and quotes around a
value are removed. A variable that is already set in the environment is never overwritten, so an exported value wins.
Values are never printed.
"""
import os
from pathlib import Path


def find_env_file(start=None):
    here = Path(start or Path.cwd()).resolve()
    for folder in (here, *list(here.parents)[:2]):
        candidate = folder / ".env"
        if candidate.is_file():
            return candidate
    return None


def load_env(start=None):
    """Set variables from the nearest .env. Returns the names that were set (never the values)."""
    path = find_env_file(start)
    if path is None:
        return []
    loaded = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        name, _, value = line.partition("=")
        name, value = name.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        elif " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        if name and value and name not in os.environ:
            os.environ[name] = value
            loaded.append(name)
    return loaded
