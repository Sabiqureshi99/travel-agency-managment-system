"""
reports/invoice_report.py
=========================
Invoice PDF generator for TAMS.

Generates professional A4 PDF invoices for customers with:
- Company letterhead
- Invoice header (number, date, due date, customer details)
- Line items table
- Totals section (subtotal, discount, tax, grand total)
- Amount in words (Pakistani Rupees)
- Payment instructions footer
- Stamp area
"""
from __future__ import annotations

import io
import logging
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)


class InvoiceReport:
    """
    Generates a professional PDF invoice using ReportLab.

    Usage::

        report = InvoiceReport()
        pdf_bytes = report.generate(invoice_data)
        # Save or display pdf_bytes
    """

    def generate(self, invoice_data: dict[str, Any]) -> bytes:
        """
        Generate a PDF invoice.

        Args:
            invoice_data: Dict containing:
                - invoice_number, invoice_date, due_date
                - customer_name, customer_phone, customer_address
                - items: [{description, quantity, unit_price, total}]
                - subtotal, discount, tax_amount, total_amount, amount_paid, amount_remaining
                - currency, notes

        Returns:
            PDF file as bytes.
        """
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable, KeepTogether
        )
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
        from config.settings import settings
        from utils.formatters import format_currency, format_date, number_to_words_pkr

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        styles = getSampleStyleSheet()
        story: list = []

        # ---------------------------------------------------------------
        # HEADER
        # ---------------------------------------------------------------
        accent = colors.HexColor("#4F46E5")
        dark_text = colors.HexColor("#1E293B")
        gray_text = colors.HexColor("#6B7280")

        company = settings.company
        currency = invoice_data.get("currency", settings.currency.default)

        header_data = [
            [
                # Left: Company info
                Paragraph(
                    f"""<font size="16" color="#4F46E5"><b>{company.name}</b></font><br/>
                    <font size="9" color="#6B7280">
                    {company.address}<br/>
                    Tel: {company.phone}<br/>
                    Email: {company.email}<br/>
                    NTN: {company.ntn or 'N/A'}
                    </font>""",
                    styles["Normal"],
                ),
                # Right: INVOICE title + number
                Paragraph(
                    f"""<font size="28" color="#4F46E5"><b>INVOICE</b></font><br/>
                    <font size="10" color="#374151">
                    <b>Invoice#:</b> {invoice_data.get('invoice_number', '')}<br/>
                    <b>Date:</b> {format_date(invoice_data.get('invoice_date'))}<br/>
                    <b>Due Date:</b> {format_date(invoice_data.get('due_date', ''))}<br/>
                    <b>Status:</b> {invoice_data.get('status', 'Unpaid')}
                    </font>""",
                    ParagraphStyle("right", parent=styles["Normal"], alignment=TA_RIGHT),
                ),
            ]
        ]
        header_table = Table(header_data, colWidths=["50%", "50%"])
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(header_table)
        story.append(HRFlowable(width="100%", thickness=2, color=accent))
        story.append(Spacer(1, 5 * mm))

        # ---------------------------------------------------------------
        # BILL TO
        # ---------------------------------------------------------------
        bill_to_data = [
            [
                Paragraph(
                    f"""<b>Bill To:</b><br/>
                    <font size="11"><b>{invoice_data.get('customer_name', '')}</b></font><br/>
                    <font size="9" color="#6B7280">
                    {invoice_data.get('customer_phone', '')}<br/>
                    {invoice_data.get('customer_address', '')}
                    </font>""",
                    styles["Normal"],
                ),
                "",
            ]
        ]
        bill_to_table = Table(bill_to_data, colWidths=["60%", "40%"])
        story.append(bill_to_table)
        story.append(Spacer(1, 6 * mm))

        # ---------------------------------------------------------------
        # LINE ITEMS TABLE
        # ---------------------------------------------------------------
        item_headers = ["#", "Description", "Qty", "Unit Price", "Total"]
        item_rows = []
        items = invoice_data.get("items", [])
        for idx, item in enumerate(items, 1):
            item_rows.append([
                str(idx),
                str(item.get("description", "")),
                str(item.get("quantity", 1)),
                format_currency(float(item.get("unit_price", 0)), currency),
                format_currency(float(item.get("total", 0)), currency),
            ])

        items_data = [item_headers] + item_rows
        col_widths = [10 * mm, 80 * mm, 20 * mm, 35 * mm, 35 * mm]
        items_table = Table(items_data, colWidths=col_widths, repeatRows=1)
        items_table.setStyle(TableStyle([
            # Header
            ("BACKGROUND", (0, 0), (-1, 0), accent),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            # Data
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("ALIGN", (0, 1), (0, -1), "CENTER"),
            ("ALIGN", (2, 1), (2, -1), "CENTER"),
            ("ALIGN", (3, 1), (4, -1), "RIGHT"),
            ("TOPPADDING", (0, 1), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 4 * mm))

        # ---------------------------------------------------------------
        # TOTALS
        # ---------------------------------------------------------------
        subtotal = float(invoice_data.get("subtotal", 0))
        discount = float(invoice_data.get("discount", 0))
        tax = float(invoice_data.get("tax_amount", 0))
        total = float(invoice_data.get("total_amount", 0))
        paid = float(invoice_data.get("amount_paid", 0))
        remaining = float(invoice_data.get("amount_remaining", 0))

        totals_data = [
            ["", "Subtotal:", format_currency(subtotal, currency)],
            ["", "Discount:", f"- {format_currency(discount, currency)}"],
            ["", "Tax:", format_currency(tax, currency)],
            ["", "TOTAL:", format_currency(total, currency)],
            ["", "Amount Paid:", format_currency(paid, currency)],
            ["", "Amount Due:", format_currency(remaining, currency)],
        ]
        totals_table = Table(totals_data, colWidths=["60%", "25%", "15%"])
        totals_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("ALIGN", (2, 0), (2, -1), "RIGHT"),
            ("FONTNAME", (1, 3), (2, 3), "Helvetica-Bold"),
            ("FONTSIZE", (1, 3), (2, 3), 11),
            ("BACKGROUND", (1, 3), (2, 3), accent),
            ("TEXTCOLOR", (1, 3), (2, 3), colors.white),
            ("FONTNAME", (1, 5), (2, 5), "Helvetica-Bold"),
            ("TEXTCOLOR", (2, 5), (2, 5), colors.HexColor("#DC2626")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(totals_table)
        story.append(Spacer(1, 4 * mm))

        # ---------------------------------------------------------------
        # AMOUNT IN WORDS
        # ---------------------------------------------------------------
        try:
            words = number_to_words_pkr(total)
        except Exception:
            words = f"{currency} {total:.2f}"

        amount_words_style = ParagraphStyle(
            "AmountWords",
            parent=styles["Normal"],
            fontSize=9,
            textColor=gray_text,
            borderPad=6,
        )
        story.append(
            Paragraph(f"<b>Amount in Words:</b> {words}", amount_words_style)
        )
        story.append(Spacer(1, 4 * mm))

        # ---------------------------------------------------------------
        # NOTES
        # ---------------------------------------------------------------
        notes = invoice_data.get("notes", "")
        if notes:
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0")))
            story.append(Spacer(1, 3 * mm))
            story.append(Paragraph(f"<b>Notes:</b> {notes}", styles["Normal"]))
            story.append(Spacer(1, 3 * mm))

        # ---------------------------------------------------------------
        # FOOTER
        # ---------------------------------------------------------------
        story.append(HRFlowable(width="100%", thickness=1, color=accent))
        story.append(Spacer(1, 3 * mm))
        footer_style = ParagraphStyle(
            "Footer",
            parent=styles["Normal"],
            fontSize=8,
            textColor=gray_text,
            alignment=TA_CENTER,
        )
        story.append(
            Paragraph(
                f"Thank you for choosing {company.name}. "
                "For queries, please contact us at "
                f"{company.phone} or {company.email}",
                footer_style,
            )
        )

        doc.build(story)
        return buffer.getvalue()
