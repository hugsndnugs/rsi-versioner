"""Verse Switcher: swap LIVE/PTU folders with safety checks."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("verse-switcher")
except PackageNotFoundError:
    __version__ = "0.0.0"
