"""Module with report classes."""

# Python Libraries
from abc import ABC
from typing import Any, Dict

from fpdf import FPDF


class HumasolReport(ABC, FPDF):
    """Base class for Humasol reports.

    Class contains methods for styling and common functionality.
    """

    # TODO: add correct parameter values
    # TODO: implement functionality

    font_type = "Arial"
    font_sizes = {"regular": 11, "title": 14, "subtitle": 12}
    logo = "path/logo.png"
    colors = {"orange": "hex", "brown": "hex", "pink": "hex"}
    margins = list[int]()

    def __init__(self, *_, **__) -> None:
        """Initialize a report object."""
        super().__init__()
        self.data: Dict[str, Any]

    def create_report(self, data) -> str:
        """Create the PDF."""

    def _add_image(self, image: Dict) -> None:
        """Add an image to this report."""

    def _add_page(self) -> None:
        """Add a page to this report."""

    def _create_header(self, name: str) -> None:
        """Create a page header."""


class EnergyReport(HumasolReport):
    """Energy system report class."""

    # TODO: implement functionality
