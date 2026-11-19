"""Locate the Boundary.IQ parcel-engine and put it on sys.path.

The engine is the single source of truth for survey math - bearings, traverse,
closure, curves, ring verification. Nothing in this package reimplements it.
It lives outside this repo (it carries client data and its own history), so it
is resolved at import time rather than vendored.

Resolution order:
    1. $BOUNDARY_IQ_ENGINE          - path to the parcel-engine directory
    2. ~/boundary.iq.r2/parcel-engine
    3. ../boundary.iq.r2/parcel-engine relative to this repo

Set the env var if yours is elsewhere:
    export BOUNDARY_IQ_ENGINE=/path/to/boundary.iq.r2/parcel-engine
"""
import os
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _candidates():
    env = os.environ.get("BOUNDARY_IQ_ENGINE")
    if env:
        yield env
    home = os.path.expanduser("~")
    yield os.path.join(home, "boundary.iq.r2", "parcel-engine")
    yield os.path.abspath(os.path.join(_REPO, "..", "boundary.iq.r2", "parcel-engine"))


def engine_path():
    """Absolute path to the parcel-engine directory, or raise with guidance."""
    tried = []
    for c in _candidates():
        tried.append(c)
        if os.path.isfile(os.path.join(c, "engine", "cogo.py")):
            return os.path.abspath(c)
    raise ImportError(
        "Boundary.IQ parcel-engine not found. Looked in:\n  "
        + "\n  ".join(tried)
        + "\nSet BOUNDARY_IQ_ENGINE to the parcel-engine directory."
    )


def ensure_on_path():
    """Idempotently add the engine to sys.path. Returns its path."""
    p = engine_path()
    if p not in sys.path:
        sys.path.insert(0, p)
    return p
