"""
services/invoice_generator.py
==============================
ReportLab PDF invoice generator for TAMS.

Provides two public methods:

* ``generate_invoice_pdf`` — legacy itemised invoice (per-pax rows).
  Still used for flight-only, hotel-only, and other non-group bookings.

* ``generate_umrah_group_invoice_pdf`` — Phase 4 group invoice that
  groups base-package billing lines by PAX type (Adult / Child / Infant),
  shows the unit price per category, the category subtotal, then appends
  flight / visa / hotel / transport lines exactly as before.
  The Grand Total at the bottom always matches the live UI totals because
  both are derived from the same categorical payload values.
"""
import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image,
    KeepTogether,
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.utils import ImageReader

from services.company_profile_service import CompanyProfileService

# ---------------------------------------------------------------------------
# Colour palette (matches the dark-theme UI)
# ---------------------------------------------------------------------------
_COLOR_ADULT  = colors.HexColor("#1D4E89")   # deep blue
_COLOR_CHILD  = colors.HexColor("#145A32")   # forest green
_COLOR_INFANT = colors.HexColor("#7D6608")   # amber/dark-gold
_COLOR_HEADER = colors.HexColor("#1A1A2E")   # near-black header
_COLOR_ALT    = colors.HexColor("#F4F6F7")   # alternate row tint
_COLOR_TOTAL  = colors.HexColor("#1B2631")   # grand-total row bg
_COLOR_WHITE  = colors.white
_COLOR_BLACK  = colors.black

# Maps description prefix → category colour
_TIER_COLORS: dict[str, object] = {
    "Adult":  _COLOR_ADULT,
    "Child":  _COLOR_CHILD,
    "Infant": _COLOR_INFANT,
}


class InvoiceGenerator:
    """Generates PDF invoices matching the TAMS reference format."""

    # ------------------------------------------------------------------ #
    # Shared helpers                                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_header(doc_width: float, styles, profile=None):
        """Return (logo_flowable, header_text, sub_header_text) tuple."""
        header_style = ParagraphStyle(
            "HeaderStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            alignment=TA_CENTER,
        )
        sub_header_style = ParagraphStyle(
            "SubHeaderStyle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            alignment=TA_CENTER,
            leading=12,
        )

        if profile is None:
            profile = CompanyProfileService().get_profile()

        if profile:
            comp_name  = profile.company_name or "Hamza Travel & Tours Nawabshah"
            address    = profile.address      or "Tayaba Center, Nawabshah, Sindh, Pakistan"
            phone      = profile.phone        or ""
            logo_data  = profile.logo_data
        else:
            comp_name  = "Hamza Travel & Tours Nawabshah"
            address    = "Tayaba Center, Nawabshah, Sindh, Pakistan"
            phone      = ""
            logo_data  = None

        header_text     = f"<b>{comp_name}</b>"
        sub_header_text = f"Address : {address}"
        if phone:
            sub_header_text += f"<br/>Phone : {phone}"

        if logo_data:
            image_stream = io.BytesIO(logo_data)
            reader = ImageReader(image_stream)
            orig_w, orig_h = reader.getSize()
            max_h = 75
            logo_w = max_h * (orig_w / float(orig_h))
            image_stream.seek(0)
            logo_flowable = Image(image_stream, width=logo_w, height=max_h)
        else:
            logo_flowable = Paragraph(
                "<font size=10 color='#6B7280'>No Logo</font>", styles["Normal"]
            )

        return (
            logo_flowable,
            Paragraph(header_text, header_style),
            Paragraph(sub_header_text, sub_header_style),
        )

    @staticmethod
    def _build_footer(styles):
        """Return a list of footer flowables."""
        footer_style = ParagraphStyle(
            "FooterStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            alignment=TA_LEFT,
        )
        disclaimer_style = ParagraphStyle(
            "DisclaimerStyle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
        )
        disclaimer_right_style = ParagraphStyle(
            "DisclaimerRightStyle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            alignment=TA_RIGHT,
        )
        footer_text = (
            f"PRINTED BY CLIENT: {datetime.now().strftime('%d-%m-%Y - %H:%M:%S')}"
        )
        disclaimer_text = (
            "On payment an official receipt should be obtained immediately.<br/>"
            "Company will not hold responsibility for any payment without receipt.<br/>"
            "This is system generated invoice and does not require any signature"
        )
        disclaimer_right = "E. &amp; O.E.<br/>Hamza Travel &amp; Tours Nawabshah"

        bottom_table = Table(
            [[Paragraph(disclaimer_text, disclaimer_style),
              Paragraph(disclaimer_right, disclaimer_right_style)]],
            colWidths=[4 * inch, 3 * inch],
        )
        bottom_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))

        return [
            HRFlowable(width="100%", thickness=1, color=_COLOR_BLACK, spaceAfter=5, spaceBefore=5),
            Paragraph(footer_text, footer_style),
            HRFlowable(width="100%", thickness=1, color=_COLOR_BLACK, spaceAfter=15, spaceBefore=5),
            bottom_table,
        ]

    # ------------------------------------------------------------------ #
    # Legacy itemised invoice (unchanged public API)                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def generate_invoice_pdf(invoice, filepath, is_package_summary=False, package_name="Umrah Package"):
        """
        Generate a PDF for the given Invoice object.

        Original per-row itemised format — unchanged from pre-Phase-4.
        """
        from typing import Any
        from reportlab.platypus.flowables import Flowable

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=30, leftMargin=30,
            topMargin=30,   bottomMargin=30,
        )
        elements: list[Flowable] = []
        styles = getSampleStyleSheet()

        # ── Header ────────────────────────────────────────────────────
        logo_flowable, header_para, sub_header_para = InvoiceGenerator._build_header(
            doc.width, styles
        )
        header_table = Table(
            [[logo_flowable, [header_para, sub_header_para]]],
            colWidths=[2.5 * inch, 4 * inch],
        )
        header_table.setStyle(TableStyle([
            ("ALIGN",  (0, 0), (0, 0), "LEFT"),
            ("ALIGN",  (1, 0), (1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 0.5 * inch))

        # ── Customer / Invoice info ────────────────────────────────────
        info_style = ParagraphStyle(
            "InfoStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
        )
        customer_name     = (invoice.customer.full_name or "").upper() if invoice.customer else "CASH CUSTOMER"
        customer_passport = (invoice.customer.passport_number or "").upper() if (invoice.customer and invoice.customer.passport_number) else "N/A"
        issue_date_str    = invoice.issue_date.strftime("%d/%m/%Y") if invoice.issue_date else ""

        # Fetch group and pax details if this is a custom umrah booking
        total_pax = 0
        adults = 0
        child = 0
        infants = 0
        group_name = ""
        booking_no = ""
        
        if getattr(invoice, "reference_type", "") == "CustomUmrahBooking" and getattr(invoice, "reference_id", ""):
            from config.database import get_session
            from models.umrah import CustomUmrahBooking
            with get_session() as session:
                umrah_booking = session.get(CustomUmrahBooking, invoice.reference_id)
                if umrah_booking:
                    total_pax = int(getattr(umrah_booking, "total_pilgrims", 0) or 0)
                    booking_no = getattr(umrah_booking, "booking_number", "") or ""
                    
                    if umrah_booking.pilgrims:
                        for p in umrah_booking.pilgrims:
                            if p.group_no:
                                group_name = p.group_no
                            ptype = getattr(p, 'pax_type', 'Adult').lower()
                            if ptype == 'child':
                                child += 1
                            elif ptype == 'infant':
                                infants += 1
                            else:
                                adults += 1
                                
                    if adults == 0 and child == 0 and infants == 0:
                        from models.booking import Booking as MasterBooking
                        master = session.query(MasterBooking).filter_by(package_id=umrah_booking.id, is_deleted=False).first()
                        if master:
                            adults = int(master.adult_count or 0)
                            child = int(master.child_count or 0)
                            infants = int(master.infant_count or 0)
                            
                    if not group_name and invoice.customer:
                        group_name = f"{invoice.customer.full_name} GROUP"

        if not group_name:
            group_name = getattr(invoice, "group_code", "") or "N/A"
            
        pax_str = f"{total_pax or 'N/A'}"
        if total_pax > 0:
            pax_str += f" (Adult: {adults}, Child: {child}, Infant: {infants})"

        info_data: list[list[Any]] = [
            [Paragraph(f"<b>Group Name: {group_name}</b>", info_style),
             Paragraph(f"<b>INVOICE NO : \t\t{invoice.invoice_number}</b>", info_style)],
            [Paragraph(f"<b>Customer: {customer_name}</b>", info_style),
             Paragraph(f"<b>INVOICE DATE : \t\t{issue_date_str}</b>", info_style)],
            [Paragraph(f"<b>Passport: {customer_passport}</b>", info_style),
             Paragraph(f"<b>TOTAL PAX : \t\t{pax_str}</b>", info_style)],
            [Paragraph(f"<b>Booking Ref: {booking_no}</b>", info_style), ""],
        ]
        info_table = Table(info_data, colWidths=[3.5 * inch, 3 * inch])
        info_table.setStyle(TableStyle([
            ("ALIGN",  (0, 0), (0, -1), "LEFT"),
            ("ALIGN",  (1, 0), (1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.3 * inch))

        # ── Title ─────────────────────────────────────────────────────
        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Normal"],
            fontName="Times-Bold",
            fontSize=18,
            alignment=TA_CENTER,
            spaceBefore=20,
            spaceAfter=15,
        )
        elements.append(Paragraph("INVOICE", title_style))

        # ── Items table ───────────────────────────────────────────────
        table_cell_style = ParagraphStyle(
            "TableCellStyle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            alignment=TA_LEFT,
        )
        table_data: list[list[Any]] = [
            ["S.NO", "PASSENGER NAME", "PASSPORT", "DETAILS", "TOTAL"]
        ]

        if is_package_summary:
            details = f"MASTER PACKAGE - {package_name}".upper() if package_name else "MASTER PACKAGE"
            table_data.append([
                "1",
                Paragraph(customer_name, table_cell_style),
                customer_passport,
                Paragraph(details, table_cell_style),
                f"{(invoice.subtotal or 0):,.0f}",
            ])
        else:
            for i, item in enumerate(invoice.items, start=1):
                raw_p_name = getattr(item, "passenger_name", None)
                raw_p_pass = getattr(item, "passport_number", None)
                p_name     = raw_p_name.upper() if raw_p_name else customer_name
                p_passport = raw_p_pass.upper() if raw_p_pass else customer_passport
                details    = (item.description or "").upper()
                table_data.append([
                    str(i),
                    Paragraph(p_name, table_cell_style),
                    p_passport,
                    Paragraph(details.replace("\n", "<br/>"), table_cell_style),
                    f"{(item.total_price or 0):,.0f}",
                ])

        table_data.append(["", "", "", "T O T A L",       f"{(invoice.subtotal or 0):,.0f}"])
        table_data.append(["", "", "", "G R A N D   T O T A L", f"{(invoice.total_amount or 0):,.0f}"])

        main_table = Table(table_data, colWidths=[35, 120, 70, 210, 100])
        row_count = len(table_data)
        sub_row   = row_count - 2
        grand_row = row_count - 1

        ts_cmds = [
            ("BACKGROUND", (0, 0),  (-1, 0),               _COLOR_HEADER),
            ("TEXTCOLOR",  (0, 0),  (-1, 0),               _COLOR_WHITE),
            ("FONTNAME", (0, 0),  (-1, 0),               "Helvetica-Bold"),
            ("FONTSIZE", (0, 0),  (-1, -1),               9),
            ("ALIGN",    (0, 0),  (-1, -1),               "CENTER"),
            ("ALIGN",    (1, 1),  (1, sub_row - 1),       "LEFT"),
            ("ALIGN",    (3, 1),  (3, sub_row - 1),       "LEFT"),
            ("ALIGN",    (4, 0),  (4, -1),                "RIGHT"),
            ("VALIGN",   (0, 0),  (-1, -1),               "MIDDLE"),
            ("GRID",     (0, 0),  (-1, sub_row - 1),      0.5, colors.grey),
            ("BOX",      (0, 0),  (-1, -1),               1, _COLOR_BLACK),
            
            # Subtotal row
            ("SPAN",     (0, sub_row),   (2, sub_row)),
            ("ALIGN",    (3, sub_row),   (3, sub_row),    "RIGHT"),
            ("FONTNAME", (3, sub_row),   (4, sub_row),    "Helvetica-Bold"),
            ("BOX",      (0, sub_row),   (-1, sub_row),   1, _COLOR_BLACK),
            ("INNERGRID",(3, sub_row),   (4, sub_row),    1, _COLOR_BLACK),
            
            # Grand total row
            ("BACKGROUND",(0, grand_row), (-1, grand_row), _COLOR_TOTAL),
            ("TEXTCOLOR", (0, grand_row), (-1, grand_row), _COLOR_WHITE),
            ("SPAN",      (0, grand_row), (2, grand_row)),
            ("ALIGN",     (3, grand_row), (3, grand_row),  "RIGHT"),
            ("FONTNAME",  (3, grand_row), (4, grand_row),  "Helvetica-Bold"),
            ("BOX",       (0, grand_row), (-1, grand_row), 1, _COLOR_BLACK),
            ("INNERGRID", (3, grand_row), (4, grand_row),  1, _COLOR_BLACK),
        ]
        
        # Apply alternate tints for data rows (index 1 up to sub_row - 1)
        for row_idx in range(1, sub_row):
            if row_idx % 2 == 0:
                ts_cmds.append(("BACKGROUND", (0, row_idx), (-1, row_idx), _COLOR_ALT))
                
        main_table.setStyle(TableStyle(ts_cmds))
        elements.append(main_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Amount in words
        try:
            amount_words = InvoiceGenerator._amount_to_words(int(invoice.total_amount or 0))
            words_style = ParagraphStyle(
                "WordsStyle",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=9,
            )
            elements.append(
                Paragraph(f"Amount in Words: {amount_words} Rupees Only", words_style)
            )
            elements.append(Spacer(1, 0.15 * inch))
        except Exception:
            pass

        elements.extend(InvoiceGenerator._build_footer(styles))
        doc.build(elements)
        return filepath

    # ------------------------------------------------------------------ #
    # Phase 4 — Group invoice with categorical PAX-type breakdown          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def generate_umrah_group_invoice_pdf(invoice, filepath, umrah_booking=None):
        """
        Generate a grouped Umrah group invoice PDF.

        Layout
        ------
        Standard header + customer info block, then an INVOICE title,
        then a **grouped items table** with:

        ┌────────────────────────────────────────────────────────┐
        │  #  │  CATEGORY                  │  QTY │  UNIT  │ TOTAL │
        ├─────┼────────────────────────────┼──────┼────────┼───────┤
        │  1  │ Umrah Package — Adult (x8) │   8  │ 55,000 │ 4,40,000│ ← blue header
        │  2  │ Umrah Package — Child (x1) │   1  │ 40,000 │  40,000 │ ← green header
        │  3  │ Umrah Package — Infant (x1)│   1  │ 15,000 │  15,000 │ ← amber header
        │  4  │ Flight [Outbound] (PIA)    │  10  │ 22,000 │ 2,20,000│
        │ … │ …                            │  …   │    …   │    …    │
        ├─────┴────────────────────────────┴──────┴────────┤  TOTAL │
        ├─────────────────────────────────────────────────── GRAND TOTAL ─┤
        └──────────────────────────────────────────────────────────────────┘

        The Grand Total is always the arithmetic sum of all line totals —
        perfectly matching the live UI ``lbl_live_grand_total`` label.

        Parameters
        ----------
        invoice : Invoice ORM object
            The invoice to render.  ``invoice.items`` is used to get the
            individual line items.
        filepath : str
            Absolute path where the PDF should be written.
        umrah_booking : CustomUmrahBooking | None
            Optional — used to extract booking metadata (group size, etc.)
            for the header info block.

        Returns
        -------
        str
            The filepath passed in (for chaining).
        """
        from typing import Any
        from reportlab.platypus.flowables import Flowable

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=30, leftMargin=30,
            topMargin=30,   bottomMargin=30,
        )
        elements: list[Flowable] = []
        styles = getSampleStyleSheet()

        # ── Styles ────────────────────────────────────────────────────
        cell_style = ParagraphStyle(
            "CellStyle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            alignment=TA_LEFT,
        )
        cell_bold = ParagraphStyle(
            "CellBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            alignment=TA_LEFT,
        )
        info_style = ParagraphStyle(
            "InfoStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
        )
        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Normal"],
            fontName="Times-Bold",
            fontSize=18,
            alignment=TA_CENTER,
            spaceBefore=20,
            spaceAfter=15,
        )

        # ── Header ─────────────────────────────────────────────────
        logo_flowable, header_para, sub_header_para = InvoiceGenerator._build_header(
            doc.width, styles
        )
        header_tbl = Table(
            [[logo_flowable, [header_para, sub_header_para]]],
            colWidths=[2.5 * inch, 4 * inch],
        )
        header_tbl.setStyle(TableStyle([
            ("ALIGN",  (0, 0), (0, 0), "LEFT"),
            ("ALIGN",  (1, 0), (1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(header_tbl)
        elements.append(Spacer(1, 0.4 * inch))

        # ── Customer / Invoice info ────────────────────────────────
        customer        = invoice.customer
        customer_name   = (customer.full_name or "").upper() if customer else "CASH CUSTOMER"
        customer_pass   = (customer.passport_number or "").upper() if (customer and customer.passport_number) else "N/A"
        issue_date_str  = invoice.issue_date.strftime("%d/%m/%Y") if invoice.issue_date else ""

        # Group size from booking or inferred from items
        total_pax = 0
        adults = 0
        child = 0
        infants = 0
        group_name = ""
        booking_no = ""
        
        if umrah_booking:
            total_pax = int(getattr(umrah_booking, "total_pilgrims", 0) or 0)
            booking_no = getattr(umrah_booking, "booking_number", "") or ""
            
            # 1. Fetch from pilgrims list
            if umrah_booking.pilgrims:
                for p in umrah_booking.pilgrims:
                    if p.group_no:
                        group_name = p.group_no
                    ptype = getattr(p, 'pax_type', 'Adult').lower()
                    if ptype == 'child':
                        child += 1
                    elif ptype == 'infant':
                        infants += 1
                    else:
                        adults += 1
            
            # 2. Fallback to master booking if no pilgrims are found (or 0 counted)
            if adults == 0 and child == 0 and infants == 0:
                from config.database import get_session
                from models.booking import Booking as MasterBooking
                with get_session() as session:
                    master = session.query(MasterBooking).filter_by(package_id=umrah_booking.id, is_deleted=False).first()
                    if master:
                        adults = int(master.adult_count or 0)
                        child = int(master.child_count or 0)
                        infants = int(master.infant_count or 0)
            
            if not group_name and customer:
                group_name = f"{customer.full_name} GROUP"

        if not group_name:
            group_name = getattr(invoice, "group_code", "") or "N/A"
            
        pax_str = f"{total_pax or 'N/A'}"
        if total_pax > 0:
            pax_str += f" (Adult: {adults}, Child: {child}, Infant: {infants})"

        info_data: list[list[Any]] = [
            [Paragraph(f"<b>Group Name: {group_name}</b>", info_style),
             Paragraph(f"<b>INVOICE NO : {invoice.invoice_number}</b>", info_style)],
            [Paragraph(f"<b>Customer: {customer_name}</b>", info_style),
             Paragraph(f"<b>INVOICE DATE : {issue_date_str}</b>", info_style)],
            [Paragraph(f"<b>Passport: {customer_pass}</b>", info_style),
             Paragraph(f"<b>TOTAL PAX : {pax_str}</b>", info_style)],
            [Paragraph(f"<b>Booking Ref: {booking_no}</b>", info_style), ""],
        ]
        info_tbl = Table(info_data, colWidths=[3.5 * inch, 3 * inch])
        info_tbl.setStyle(TableStyle([
            ("ALIGN",  (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(info_tbl)
        elements.append(Spacer(1, 0.25 * inch))
        elements.append(Paragraph("GROUP INVOICE", title_style))

        # ── Items table columns ───────────────────────────────────
        # S.NO | SERVICE DESCRIPTION | QTY | UNIT PRICE (PKR) | TOTAL (PKR)
        col_widths = [35, 220, 45, 90, 90]

        def _hdr_cell(text: str) -> Paragraph:
            return Paragraph(
                f"<font color='white'><b>{text}</b></font>", cell_bold
            )

        table_data: list[list[Any]] = [[
            _hdr_cell("S.NO"),
            _hdr_cell("SERVICE DESCRIPTION"),
            _hdr_cell("QTY"),
            _hdr_cell("UNIT PRICE\n(PKR)"),
            _hdr_cell("TOTAL\n(PKR)"),
        ]]

        # Accumulate total for verification
        computed_grand_total = 0.0

        # ── Tier colour map (description prefix → color) ──────────
        def _tier_color_for_item(description: str):
            desc_upper = (description or "").upper()
            for tier in ("ADULT", "CHILD", "INFANT"):
                if tier in desc_upper:
                    return _TIER_COLORS.get(tier.capitalize())
            return None

        # ── Render invoice items ──────────────────────────────────
        row_styles: list[tuple] = []
        data_start = 1  # header at index 0

        for idx, item in enumerate(invoice.items, start=1):
            desc_raw  = item.description or ""
            qty       = int(item.quantity or 1)
            unit_px   = float(item.unit_price or 0)
            total_px  = float(item.total_price or 0)
            computed_grand_total += total_px

            # Detect if this is a categorical PAX tier row
            tier_color = _tier_color_for_item(desc_raw)

            desc_text  = desc_raw.upper()
            unit_str   = f"{unit_px:,.0f}"
            total_str  = f"{total_px:,.0f}"

            if tier_color:
                # Render description in white-on-colour badge style
                desc_cell = Paragraph(
                    f"<font color='white'><b>{desc_text}</b></font>", cell_bold
                )
            else:
                desc_cell = Paragraph(desc_text, cell_style)

            table_data.append([
                str(idx),
                desc_cell,
                str(qty),
                unit_str,
                total_str,
            ])

            # Tag the row for styling
            row_idx = len(table_data) - 1
            row_styles.append(("tier_row", row_idx, tier_color))

        # ── Totals rows ───────────────────────────────────────────
        subtotal_row_idx     = len(table_data)
        grand_total_row_idx  = len(table_data) + 1

        subtotal_amount  = float(invoice.subtotal      or 0)
        gt_amount        = float(invoice.total_amount  or 0)

        table_data.append(["", "", "", Paragraph("<b>SUBTOTAL</b>", cell_bold),     f"{subtotal_amount:,.0f}"])
        table_data.append(["", "", "", Paragraph("<b>GRAND TOTAL</b>", cell_bold),  f"{gt_amount:,.0f}"])

        # ── Build TableStyle ──────────────────────────────────────
        ts_cmds = [
            # Header row
            ("BACKGROUND",  (0, 0),              (-1, 0),                  _COLOR_HEADER),
            ("TEXTCOLOR",   (0, 0),              (-1, 0),                  _COLOR_WHITE),
            ("FONTNAME",    (0, 0),              (-1, 0),                  "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0),              (-1, -1),                  9),
            ("ALIGN",       (0, 0),              (-1, -1),                  "CENTER"),
            ("ALIGN",       (1, data_start),     (1, subtotal_row_idx - 1), "LEFT"),
            ("ALIGN",       (3, data_start),     (4, -1),                   "RIGHT"),
            ("VALIGN",      (0, 0),              (-1, -1),                  "MIDDLE"),
            # Grid
            ("GRID",        (0, 0),              (-1, subtotal_row_idx - 1), 0.5, colors.grey),
            ("BOX",         (0, 0),              (-1, -1),                   1,   _COLOR_BLACK),
            # Subtotal row
            ("SPAN",        (0, subtotal_row_idx),    (2, subtotal_row_idx)),
            ("ALIGN",       (3, subtotal_row_idx),    (3, subtotal_row_idx),    "RIGHT"),
            ("FONTNAME",    (3, subtotal_row_idx),    (4, subtotal_row_idx),    "Helvetica-Bold"),
            ("BOX",         (0, subtotal_row_idx),    (-1, subtotal_row_idx),   1,   _COLOR_BLACK),
            ("INNERGRID",   (3, subtotal_row_idx),    (4, subtotal_row_idx),    1,   _COLOR_BLACK),
            # Grand total row
            ("BACKGROUND",  (0, grand_total_row_idx), (-1, grand_total_row_idx), _COLOR_TOTAL),
            ("TEXTCOLOR",   (0, grand_total_row_idx), (-1, grand_total_row_idx), _COLOR_WHITE),
            ("SPAN",        (0, grand_total_row_idx), (2, grand_total_row_idx)),
            ("ALIGN",       (3, grand_total_row_idx), (3, grand_total_row_idx),  "RIGHT"),
            ("FONTNAME",    (3, grand_total_row_idx), (4, grand_total_row_idx),  "Helvetica-Bold"),
            ("BOX",         (0, grand_total_row_idx), (-1, grand_total_row_idx), 1,  _COLOR_BLACK),
            ("INNERGRID",   (3, grand_total_row_idx), (4, grand_total_row_idx),  1,  _COLOR_BLACK),
        ]

        # Apply tier colours
        for tag, row_idx, tier_color in row_styles:
            if tier_color is not None:
                ts_cmds.append(("BACKGROUND", (0, row_idx), (-1, row_idx), tier_color))
                ts_cmds.append(("TEXTCOLOR",  (0, row_idx), (-1, row_idx), _COLOR_WHITE))
            elif row_idx % 2 == 0:
                # Alternate tint for non-tier rows
                ts_cmds.append(("BACKGROUND", (0, row_idx), (-1, row_idx), _COLOR_ALT))

        main_table = Table(table_data, colWidths=col_widths)
        main_table.setStyle(TableStyle(ts_cmds))

        elements.append(KeepTogether([main_table]))
        elements.append(Spacer(1, 0.3 * inch))

        # ── Amount in words ───────────────────────────────────────
        try:
            amount_words = InvoiceGenerator._amount_to_words(int(gt_amount))
            words_style = ParagraphStyle(
                "WordsStyle",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=9,
            )
            elements.append(
                Paragraph(f"Amount in Words: {amount_words} Rupees Only", words_style)
            )
            elements.append(Spacer(1, 0.15 * inch))
        except Exception:
            pass

        elements.extend(InvoiceGenerator._build_footer(styles))
        doc.build(elements)
        return filepath

    # ------------------------------------------------------------------ #
    # Utility: amount to words (simple PKR)                               #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _amount_to_words(amount: int) -> str:
        """Convert an integer PKR amount to English words (up to billions)."""
        if amount == 0:
            return "Zero"

        ones = [
            "", "One", "Two", "Three", "Four", "Five", "Six", "Seven",
            "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen",
            "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen",
        ]
        tens = [
            "", "", "Twenty", "Thirty", "Forty", "Fifty",
            "Sixty", "Seventy", "Eighty", "Ninety",
        ]

        def _below_1000(n: int) -> str:
            if n == 0:
                return ""
            elif n < 20:
                return ones[n]
            elif n < 100:
                return tens[n // 10] + (" " + ones[n % 10] if n % 10 else "")
            else:
                rest = _below_1000(n % 100)
                return ones[n // 100] + " Hundred" + (" " + rest if rest else "")

        parts: list[str] = []
        if amount >= 1_000_000_000:
            parts.append(_below_1000(amount // 1_000_000_000) + " Billion")
            amount %= 1_000_000_000
        if amount >= 1_000_000:
            parts.append(_below_1000(amount // 1_000_000) + " Million")
            amount %= 1_000_000
        if amount >= 1_000:
            parts.append(_below_1000(amount // 1_000) + " Thousand")
            amount %= 1_000
        if amount > 0:
            parts.append(_below_1000(amount))
        return " ".join(parts)
