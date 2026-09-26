"""
reports/base_report.py
======================
Base classes for all TAMS report generators.

Provides a common interface for generating PDFs (ReportLab) and
Excel files (openpyxl) with consistent company branding.
"""
from __future__ import annotations

import io
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class ReportColors:
    """Standard colour palette used across all reports."""
    PRIMARY = (79, 70, 229)       # #4F46E5 — Indigo accent
    DARK = (26, 29, 46)           # #1A1D2E — Dark blue
    LIGHT_GRAY = (240, 242, 245)  # #F0F2F5
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    TEXT = (44, 62, 80)           # #2C3E50
    DANGER = (220, 38, 38)        # #DC2626
    SUCCESS = (22, 163, 74)       # #16A34A
    WARNING = (217, 119, 6)       # #D97706
    HEADER_BG = (79, 70, 229)     # Same as PRIMARY for table headers
    ALTERNATE_ROW = (247, 248, 252)


class BaseReport(ABC):
    """
    Abstract base class for all TAMS reports.

    Subclasses implement ``generate_pdf()`` and ``generate_excel()``
    which return the file as bytes (suitable for saving or sending
    over a network without touching the filesystem).
    """

    def __init__(self) -> None:
        from config.settings import settings
        self.company = settings.company
        self.currency = settings.currency

    def get_company_header(self) -> dict[str, str]:
        """Return a standardised company header dict for report headers."""
        return {
            "name": self.company.name,
            "address": self.company.address,
            "phone": self.company.phone,
            "email": self.company.email,
            "website": self.company.website,
            "ntn": self.company.ntn,
        }

    @abstractmethod
    def generate_pdf(self, data: dict[str, Any]) -> bytes:
        """Generate and return a PDF file as bytes."""

    @abstractmethod
    def generate_excel(self, data: dict[str, Any]) -> bytes:
        """Generate and return an Excel file as bytes."""


class PDFMixin:
    """
    Mixin providing common ReportLab PDF building utilities.

    All PDF reports should call ``_build_header()`` first, then
    populate the story, then call ``_build_pdf()`` to render.
    """

    def _build_company_header(
        self,
        story: list,
        styles: Any,
        title: str,
        subtitle: str = "",
    ) -> None:
        """
        Add company letterhead to the top of a PDF report.

        Args:
            story:    ReportLab story list to append elements to.
            styles:   getSampleStyleSheet() result.
            title:    Report title (e.g. 'Invoice').
            subtitle: Optional subtitle (e.g. 'For April 2024').
        """
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.platypus import Paragraph, Spacer, HRFlowable
        from reportlab.lib.units import mm
        from reportlab.lib import colors

        from config.settings import settings
        company = settings.company

        # Company name
        company_style = ParagraphStyle(
            "CompanyName",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#4F46E5"),
            spaceAfter=2,
        )
        story.append(Paragraph(company.name, company_style))

        # Address + contact
        contact_style = ParagraphStyle(
            "CompanyContact",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#6B7280"),
        )
        contact_text = (
            f"{company.address} | Tel: {company.phone} | "
            f"Email: {company.email}"
        )
        story.append(Paragraph(contact_text, contact_style))
        story.append(Spacer(1, 4 * mm))
        story.append(
            HRFlowable(width="100%", thickness=2, color=colors.HexColor("#4F46E5"))
        )
        story.append(Spacer(1, 4 * mm))

        # Report title
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor("#1E293B"),
        )
        story.append(Paragraph(title, title_style))
        if subtitle:
            story.append(Paragraph(subtitle, styles["Normal"]))
        story.append(Spacer(1, 6 * mm))

    def _build_info_table(
        self, story: list, data: list[tuple[str, str]], cols: int = 2
    ) -> None:
        """
        Build a compact key-value info table (for invoice header info etc.).

        Args:
            story: ReportLab story list.
            data:  List of (label, value) tuples.
            cols:  Number of columns for the layout.
        """
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.units import mm

        # Arrange data into cols columns
        rows = []
        for i in range(0, len(data), cols):
            row = []
            for j in range(cols):
                idx = i + j
                if idx < len(data):
                    label, value = data[idx]
                    row.extend([f"{label}:", value])
                else:
                    row.extend(["", ""])
            rows.append(row)

        col_width = 40 * mm
        table = Table(rows, colWidths=[col_width, col_width] * cols)
        table.setStyle(
            TableStyle([
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#374151")),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ])
        )
        story.append(table)

    def _build_data_table(
        self,
        story: list,
        headers: list[str],
        rows: list[list[str]],
        col_widths: list | None = None,
    ) -> None:
        """
        Build a styled data table with coloured header row and alternating rows.

        Args:
            story:      ReportLab story list.
            headers:    Column header strings.
            rows:       Data rows (list of lists of strings).
            col_widths: Optional list of column widths in points.
        """
        from reportlab.platypus import Table, TableStyle, Spacer
        from reportlab.lib import colors
        from reportlab.lib.units import mm

        data = [headers] + rows
        table = Table(data, colWidths=col_widths, repeatRows=1)

        style_commands = [
            # Header
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F46E5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            # Data rows
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.white, colors.HexColor("#F8FAFC")
            ]),
            ("TOPPADDING", (0, 1), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        table.setStyle(TableStyle(style_commands))
        story.append(table)
        story.append(Spacer(1, 6 * mm))


class ExcelMixin:
    """Mixin providing common openpyxl Excel building utilities."""

    def _create_workbook_with_header(
        self,
        sheet_name: str,
        title: str,
        headers: list[str],
    ):
        """
        Create an openpyxl Workbook with a styled header row.

        Returns:
            (workbook, worksheet) tuple.
        """
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
        from config.settings import settings

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = sheet_name

        # Company header (rows 1-3)
        ws.merge_cells("A1:H1")
        ws["A1"].value = settings.company.name
        ws["A1"].font = Font(bold=True, size=14, color="4F46E5")
        ws["A1"].alignment = Alignment(horizontal="center")

        ws.merge_cells("A2:H2")
        ws["A2"].value = f"{settings.company.address} | {settings.company.phone}"
        ws["A2"].font = Font(size=9, color="6B7280")
        ws["A2"].alignment = Alignment(horizontal="center")

        ws.merge_cells("A3:H3")
        ws["A3"].value = title
        ws["A3"].font = Font(bold=True, size=12)
        ws["A3"].alignment = Alignment(horizontal="center")

        ws.append([])  # Blank row

        # Header row
        header_fill = PatternFill("solid", fgColor="4F46E5")
        header_font = Font(bold=True, color="FFFFFF", size=10)
        header_alignment = Alignment(horizontal="center", vertical="center")
        thin_border = Border(
            bottom=Side(style="thin", color="E2E8F0"),
            right=Side(style="thin", color="E2E8F0"),
        )

        ws.append(headers)
        header_row = ws.max_row
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=header_row, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
            cell.border = thin_border
            ws.column_dimensions[get_column_letter(col_num)].width = max(15, len(header) + 5)

        return wb, ws

    def _to_excel_bytes(self, wb) -> bytes:
        """Save a workbook to bytes and return."""
        buffer = io.BytesIO()
        wb.save(buffer)
        return buffer.getvalue()
