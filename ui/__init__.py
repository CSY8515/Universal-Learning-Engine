"""Presentation helpers for the Universal Learning Engine interface."""

from .dashboard import render_dashboard
from .navigation import NAVIGATION_OPTIONS, render_navigation
from .theme import apply_official_theme

__all__ = [
    "NAVIGATION_OPTIONS",
    "apply_official_theme",
    "render_dashboard",
    "render_navigation",
]
