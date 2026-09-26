import sys
import os
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image

def get_desktop_path(filename):
    """Safely find files whether running as a .py script or a compiled .exe"""
    return str(Path.home() / "Desktop" / filename)

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class VoucherBuilder:
    def __init__(self, data: dict, filename: str = "Umrah_Travel_Voucher.pdf"):
        self.data = data
        self.filename = filename
        
        software_folder = os.path.abspath(".")
        vouchers_dir = os.path.join(software_folder, "vouchers")
        os.makedirs(vouchers_dir, exist_ok=True)
        
        self.pdf_path = os.path.join(vouchers_dir, filename)
        
        self.doc = SimpleDocTemplate(
            self.pdf_path,
            pagesize=A4,
            leftMargin=30,
            rightMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        self.elements = []
        self.styles = getSampleStyleSheet()
        self._init_styles()
        
    def _init_styles(self):
        self.style_left = ParagraphStyle(name='Left', parent=self.styles['Normal'], fontName='Helvetica', fontSize=8, alignment=0)
        self.style_center = ParagraphStyle(name='Center', parent=self.styles['Normal'], fontName='Helvetica', fontSize=8, alignment=1)
        self.style_right = ParagraphStyle(name='Right', parent=self.styles['Normal'], fontName='Helvetica', fontSize=8, alignment=2)
        
        self.master_table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.2, 0.2)), # #333333
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
        ])

    def _load_company_profile(self):
        """Load company profile from DB using CompanyProfileService."""
        try:
            from services.company_profile_service import CompanyProfileService
            profile = CompanyProfileService().get_profile()
            if profile:
                return {
                    'name': profile.company_name or "TRAVEL AGENCY",
                    'address': profile.address or "",
                    'phone': profile.phone or "",
                    'email': profile.email or "",
                    'logo_data': bytes(profile.logo_data) if profile.logo_data else None,
                }
        except Exception:
            pass
        return {'name': "TRAVEL AGENCY", 'address': "", 'phone': "", 'email': "", 'logo_data': None}

    def _voucher_title(self):
        """Dynamically build the voucher title from which services are present."""
        parts = []
        if self.data.get('accommodation'):
            parts.append("HOTEL")
        if self.data.get('transport'):
            parts.append("TRANSPORT")
        if self.data.get('flights'):
            parts.append("FLIGHT")
        if self.data.get('visa_details'):
            parts.append("VISA")
        if not parts:
            parts.append("SERVICE")
        return " & ".join(parts) + " VOUCHER"

    def build_header(self):
        company = self._load_company_profile()

        # Logo
        logo_img = None
        if company['logo_data']:
            try:
                import io
                from reportlab.lib.utils import ImageReader
                stream = io.BytesIO(company['logo_data'])
                reader = ImageReader(stream)
                ow, oh = reader.getSize()
                max_h = 70
                logo_img = Image(io.BytesIO(company['logo_data']), width=max_h * (ow / oh), height=max_h)
            except Exception:
                pass

        if logo_img is None:
            logo_path = get_resource_path(os.path.join("logo", "logo.png"))
            if not os.path.exists(logo_path):
                logo_path = get_resource_path(os.path.join("assets", "logo.png"))
            if os.path.exists(logo_path):
                try:
                    from reportlab.lib.utils import ImageReader
                    reader = ImageReader(logo_path)
                    ow, oh = reader.getSize()
                    max_h = 70
                    logo_img = Image(logo_path, width=max_h * (ow / oh), height=max_h)
                except Exception:
                    pass

        if logo_img is None:
            logo_img = Paragraph("<b>[LOGO]</b>", self.style_center)

        title_text = (
            f"<b><font size=16>{company['name']}</font><br/>"
            f"<font size=12>{self._voucher_title()}</font><br/><br/>"
            f"VOUCHER NO: {self.data.get('voucher_no', 'HV-0001')}</b>"
        )

        right_header = Paragraph(title_text, self.style_center)
        header_table = Table([[logo_img, right_header]], colWidths=[100, 435])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (1,0), (1,0), 'CENTER'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        self.elements.append(header_table)
        self.elements.append(Spacer(1, 10))

        # Sub-header row
        branch = self.data.get('branch_office') or company.get('address', '') or company['name']
        left_sub = Paragraph(
            f"<b>HV ISSUE DATE:</b> {self.data.get('issue_date', '')}<br/>"
            f"<b>PKG CATEGORY:</b> {self.data.get('pkg_category', '')}",
            self.style_left
        )
        right_sub = Paragraph(
            f"<b>PRINT D/T:</b> {self.data.get('print_dt', '')}<br/>"
            f"<b>BRANCH OFFICE:</b> {branch}",
            self.style_right
        )
        sub_table = Table([[left_sub, right_sub]], colWidths=[267, 268])
        sub_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        self.elements.append(sub_table)
        self.elements.append(Spacer(1, 15))

    def build_passengers(self):
        pax_headers = ["S#", "PAX NAME(S)", "PASSPORT NO.", "GROUP"]
        pax_data = [pax_headers]
        for i, pax in enumerate(self.data.get('passengers', []), 1):
            pax_data.append([str(i), pax.get('name', ''), pax.get('passport', ''), pax.get('group', '')])

        pax_table = Table(pax_data, colWidths=[35, 200, 100, 200])
        pax_table.setStyle(self.master_table_style)
        self.elements.append(pax_table)
        self.elements.append(Spacer(1, 5))
        self.elements.append(Paragraph(f"<b>TOTAL PAX: {len(self.data.get('passengers', []))}</b>", self.style_left))
        self.elements.append(Spacer(1, 15))

    def build_accommodation(self):
        self.elements.append(Paragraph("<b>ACCOMMODATION DETAILS</b>", self.style_left))
        self.elements.append(Spacer(1, 5))

        acc_headers = ["CITY", "HN#", "HOTEL NAME(S)", "ROOM", "ROOM TYPE", "CHECK IN", "CHECK OUT", "NIGHTS"]
        acc_data = [acc_headers]
        for acc in self.data.get('accommodation', []):
            acc_data.append([
                acc.get('city', ''), acc.get('hn', ''), acc.get('hotel_name', ''),
                str(acc.get('room', '')), acc.get('room_type', ''), acc.get('check_in', ''),
                acc.get('check_out', ''), str(acc.get('nights', ''))
            ])

        acc_table = Table(acc_data, colWidths=[65, 40, 140, 40, 80, 65, 65, 40])
        acc_table.setStyle(self.master_table_style)
        self.elements.append(acc_table)
        self.elements.append(Spacer(1, 5))
        self.elements.append(Paragraph("<b>NOTE: CHECK-IN TIME: 1600 HRS &amp; CHECK-OUT TIME: 1200 NOON.</b>", self.style_left))
        self.elements.append(Spacer(1, 15))

    def build_transport(self):
        self.elements.append(Paragraph("<b>TRANSPORT DETAILS</b>", self.style_left))
        self.elements.append(Spacer(1, 5))

        trans_headers = ["SNO.", "TN#", "SERVICE", "VEHICLE", "PICK-UP DATE", "CONTACT PERSON", "BOOKING REF. NO."]
        trans_data = [trans_headers]
        for i, trans in enumerate(self.data.get('transport', []), 1):
            trans_data.append([
                str(i), trans.get('tn', ''), trans.get('service', ''), trans.get('vehicle', ''),
                trans.get('pickup_date', ''), trans.get('contact', ''), trans.get('ref_no', '')
            ])

        trans_table = Table(trans_data, colWidths=[35, 40, 110, 60, 70, 110, 110])
        trans_table.setStyle(self.master_table_style)
        self.elements.append(trans_table)
        self.elements.append(Spacer(1, 15))

    def build_flights(self):
        self.elements.append(Paragraph("<b>FLIGHT DETAILS</b>", self.style_left))
        self.elements.append(Spacer(1, 5))

        flight_headers = ["PNR", "DATE", "FLIGHT", "FROM", "TO", "DEPARTURE", "ARRIVAL"]
        flight_data = [flight_headers]
        for fl in self.data.get('flights', []):
            flight_data.append([
                fl.get('pnr', ''), fl.get('date', ''), fl.get('flight', ''),
                fl.get('from', ''), fl.get('to', ''), fl.get('dep', ''), fl.get('arr', '')
            ])

        flight_table = Table(flight_data, colWidths=[70, 70, 70, 110, 110, 50, 55])
        flight_table.setStyle(self.master_table_style)
        self.elements.append(flight_table)
        self.elements.append(Spacer(1, 20))

    def build_footer(self):
        """Build footer using Company Profile — matches original voucher style."""
        company = self._load_company_profile()

        footer_style = ParagraphStyle(
            name='Footer', parent=self.styles['Normal'],
            fontName='Helvetica-Bold', fontSize=9, alignment=1
        )
        footer_normal = ParagraphStyle(
            name='FooterNorm', parent=self.styles['Normal'],
            fontName='Helvetica', fontSize=8, alignment=1
        )

        self.elements.append(Spacer(1, 15))

        # --- Helpline header ---
        self.elements.append(Paragraph("FOR HELPLINE CONTACT NO.", footer_style))
        self.elements.append(Spacer(1, 4))

        # Phone line
        phone = company.get('phone', '')
        if phone:
            self.elements.append(Paragraph(
                f"FOR CALLING {phone} | FOR WHATS APP {phone}",
                footer_normal
            ))
            self.elements.append(Spacer(1, 3))

        # Email line
        email = company.get('email', '')
        if email:
            self.elements.append(Paragraph(f"Email: {email}", footer_normal))
            self.elements.append(Spacer(1, 3))

        self.elements.append(Spacer(1, 10))

        # --- Authorized stamp ---
        self.elements.append(Paragraph("*** AUTHORIZED ***", footer_style))
        self.elements.append(Spacer(1, 3))
        self.elements.append(Paragraph(company['name'].upper(), footer_style))
        self.elements.append(Spacer(1, 3))

        # Address line
        address = company.get('address', '')
        if address:
            self.elements.append(Paragraph(f"Address: {address}", footer_normal))
            self.elements.append(Spacer(1, 3))

        # Tel + Email compact line at bottom
        contact_parts = []
        if phone:
            contact_parts.append(f"Tel Office: {phone}")
        if email:
            contact_parts.append(f"Email: {email}")
        if contact_parts:
            self.elements.append(Paragraph(" - ".join(contact_parts), footer_normal))

    def generate(self):
        self.build_header()

        # Passengers — always shown if present
        if self.data.get('passengers'):
            self.build_passengers()

        # Only render sections that have actual data
        if self.data.get('accommodation'):
            self.build_accommodation()

        if self.data.get('transport'):
            self.build_transport()

        if self.data.get('flights'):
            self.build_flights()

        self.build_footer()

        self.doc.build(self.elements)
        print(f"Generated PDF successfully at {self.pdf_path}")
        return self.pdf_path

if __name__ == "__main__":
    dummy_data = {
        'voucher_no': 'HV-8087',
        'issue_date': '23/06/2026',
        'pkg_category': 'EXECUTIVE:ADMIN',
        'print_dt': '24-06-2026 15:43:20',
        'branch_office': 'HAMZA NAWABSHAH - UMRAH',
        'passengers': [
            {'name': 'ALI AHMED MR', 'passport': 'AB1234567', 'group': 'AL-ZIYARA GROUP'},
            {'name': 'FATIMA BINT ALI MRS', 'passport': 'AB1234568', 'group': 'AL-ZIYARA GROUP'},
        ],
        'accommodation': [
            {'city': 'MAKKAH', 'hn': '1', 'hotel_name': 'SWISSOTEL MAKKAH', 'room': 1, 'room_type': 'DOUBLE', 'check_in': '25/06/2026', 'check_out': '30/06/2026', 'nights': 5},
            {'city': 'MADINAH', 'hn': '2', 'hotel_name': 'PULLMAN ZAMZAM MADINAH', 'room': 1, 'room_type': 'DOUBLE', 'check_in': '30/06/2026', 'check_out': '05/07/2026', 'nights': 5},
        ],
        'transport': [
            {'tn': '1', 'service': 'JED-MAK', 'vehicle': 'GMC', 'pickup_date': '25/06/2026', 'contact': 'DRIVER: 0512345678', 'ref_no': 'TR-9988'},
            {'tn': '2', 'service': 'MAK-MED', 'vehicle': 'GMC', 'pickup_date': '30/06/2026', 'contact': 'DRIVER: 0512345679', 'ref_no': 'TR-9989'},
        ],
        'flights': [
            {'pnr': 'A1B2C3', 'date': '25/06/2026', 'flight': 'SV 701', 'from': 'KHI', 'to': 'JED', 'dep': '10:00', 'arr': '13:00'},
            {'pnr': 'A1B2C3', 'date': '05/07/2026', 'flight': 'SV 702', 'from': 'MED', 'to': 'KHI', 'dep': '15:00', 'arr': '21:00'},
        ]
    }
    
    builder = VoucherBuilder(dummy_data)
    builder.generate()
