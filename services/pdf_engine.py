import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from config.database import get_session
from models.company_profile import CompanyProfile
from models.accounting import Receipt
from models.vendor import VendorLedger
from sqlalchemy import select, func

class GlobalPDFEngine:
    """Enterprise PDF Engine for TAMS (Travel Agency Management System)"""
    
    def __init__(self, logo_path="assets/logo.png"):
        self.logo_path = logo_path
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(name='RightAlign', alignment=2))
        
    def _build_header(self, title: str, date_range: str) -> list:
        from typing import Any
        elements: list[Any] = []
        company_name_str = "TRAVEL AGENCY MANAGEMENT SYSTEM"
        company_details_str = "Your trusted partner in travel.<br/>Email: info@travelagency.com | Phone: +92 300 1234567<br/>Address: 123 Travel Street, Main Boulevard, City"
        logo_img = None
        
        with get_session() as session:
            profile = session.query(CompanyProfile).first()
            if profile:
                company_name_str = profile.company_name or company_name_str
                
                details = []
                contact_info = []
                if profile.phone: contact_info.append(f"Phone: {profile.phone}")
                if profile.email: contact_info.append(f"Email: {profile.email}")
                if contact_info: details.append(" | ".join(contact_info))
                if profile.address: details.append(f"Address: {profile.address}")
                if profile.ntn: details.append(f"NTN: {profile.ntn}")
                
                if details:
                    company_details_str = "<br/>".join(details)
                else:
                    company_details_str = ""
                    
                if profile.logo_data:
                    try:
                        from reportlab.lib.utils import ImageReader
                        img_stream = io.BytesIO(memoryview(profile.logo_data).tobytes())
                        reader = ImageReader(img_stream)
                        orig_width, orig_height = reader.getSize()
                        max_height = 60
                        aspect_ratio = orig_width / float(orig_height)
                        logo_w = max_height * aspect_ratio
                        
                        img_stream.seek(0)
                        logo_img = Image(img_stream, width=logo_w, height=max_height)
                        logo_img.hAlign = 'LEFT'
                    except Exception:
                        pass
        
        if not logo_img:
            if os.path.exists(self.logo_path):
                try:
                    from reportlab.lib.utils import ImageReader
                    reader = ImageReader(self.logo_path)
                    orig_width, orig_height = reader.getSize()
                    max_height = 60
                    aspect_ratio = orig_width / float(orig_height)
                    logo_w = max_height * aspect_ratio
                    
                    logo_img = Image(self.logo_path, width=logo_w, height=max_height)
                    logo_img.hAlign = 'LEFT'
                except Exception:
                    pass
                
        company_info = Paragraph(
            f"<b>{company_name_str}</b><br/>{company_details_str}",
            self.styles['Normal']
        )
        
        if logo_img:
            header_table = Table([[logo_img, company_info]], colWidths=[130, 385])
        else:
            header_table = Table([["", company_info]], colWidths=[0, 515])
            
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (1,0), (1,0), 'LEFT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 10))
        
        elements.append(Paragraph(f"<b>{title}</b>", self.styles['Heading1']))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Date Range: {date_range}", self.styles['Normal']))
        elements.append(Spacer(1, 20))
        return elements
        
    def generate_supplier_report(self, filepath: str, vendor_name: str, transactions: list, date_range: str):
        """Generates a professional Supplier (Vendor) Report tracking Payments & Bills"""
        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = self._build_header(f"Supplier Ledger Report: {vendor_name}", date_range)
        
        # Data Table Headers
        data = [["Date", "Reference", "Type", "Source", "Debit (Paid)", "Credit (Billed)", "Balance"]]
        
        running_balance = 0.0
        for txn in transactions:
            running_balance += txn.get('credit', 0) - txn.get('debit', 0)
            data.append([
                txn.get('date', ''), 
                txn.get('ref', ''), 
                txn.get('type', ''),
                txn.get('source', ''),
                f"Rs. {txn.get('debit', 0):,.2f}", 
                f"Rs. {txn.get('credit', 0):,.2f}", 
                f"Rs. {running_balance:,.2f}"
            ])
            
        table = Table(data, colWidths=[65, 75, 70, 60, 80, 80, 90])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('GRID', (0,0), (-1,-1), 1, colors.lightgrey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.white])
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 30))
        
        # Summary Block
        elements.append(Paragraph(f"<b>Final Outstanding Balance: Rs. {running_balance:,.2f}</b>", self.styles['RightAlign']))
        doc.build(elements)

    def generate_customer_report(self, filepath: str, customer_name: str, transactions: list, date_range: str):
        """Generates a comprehensive Customer Ledger Report tracking Invoices & Receipts"""
        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = self._build_header(f"Customer Ledger: {customer_name}", date_range)
        
        # Data Table Headers
        data = [["Date", "Service/Ref", "Source", "Billed (Dr)", "Paid (Cr)", "Balance"]]
        
        running_balance = 0.0
        for txn in transactions:
            running_balance += txn.get('billed', 0) - txn.get('paid', 0)
            data.append([
                txn.get('date', ''), 
                txn.get('ref', ''), 
                txn.get('source', ''),
                f"Rs. {txn.get('billed', 0):,.2f}", 
                f"Rs. {txn.get('paid', 0):,.2f}", 
                f"Rs. {running_balance:,.2f}"
            ])
            
        table = Table(data, colWidths=[70, 140, 70, 80, 80, 90])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F46E5")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('GRID', (0,0), (-1,-1), 1, colors.lightgrey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.white])
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 30))
        
        # Summary Block
        elements.append(Paragraph(f"<b>Net Dues: Rs. {running_balance:,.2f}</b>", self.styles['RightAlign']))
        doc.build(elements)

    def generate_global_customer_summary(self, filepath: str, balances: list, date_range: str = "All Time"):
        """Generates a summary report of all customers and their outstanding balances"""
        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = self._build_header("Global Customer Balances Report", date_range)
        
        # Data Table Headers
        data = [["Code", "Customer Name", "Phone", "Total Billed", "Total Paid", "Balance"]]
        
        total_outstanding = 0.0
        total_billed = 0.0
        total_paid = 0.0
        
        for b in balances:
            total_outstanding += b.get('balance', 0)
            total_billed += b.get('billed', 0)
            total_paid += b.get('paid', 0)
            data.append([
                b.get('code', ''),
                b.get('name', ''),
                b.get('phone', ''),
                f"Rs. {b.get('billed', 0):,.2f}",
                f"Rs. {b.get('paid', 0):,.2f}",
                f"Rs. {b.get('balance', 0):,.2f}"
            ])
            
        table = Table(data, colWidths=[60, 150, 80, 80, 80, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F46E5")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('GRID', (0,0), (-1,-1), 1, colors.lightgrey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.white])
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        # Calculate cash vs bank breakdown
        total_cash = 0.0
        total_bank = 0.0
        with get_session() as session:
            total_cash = session.scalar(
                select(func.coalesce(func.sum(Receipt.amount), 0.0))
                .where(Receipt.payment_method == 'Cash')
            ) or 0.0
            total_bank = session.scalar(
                select(func.coalesce(func.sum(Receipt.amount), 0.0))
                .where(Receipt.payment_method == 'Bank')
            ) or 0.0
        
        # Summary Block
        summary_data = [
            ["Overall Debit (Billed):", f"Rs. {total_billed:,.2f}"],
            ["Overall Credit (Paid):", f"Rs. {total_paid:,.2f}"],
            ["Total Paid via Cash:", f"Rs. {total_cash:,.2f}"],
            ["Total Paid via Bank:", f"Rs. {total_bank:,.2f}"],
            ["Total Market Receivables:", f"Rs. {total_outstanding:,.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[150, 150], hAlign='RIGHT')
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0,-1), (-1,-1), colors.HexColor("#4F46E5")), # Highlight the final balance
        ]))
        elements.append(summary_table)
        
        doc.build(elements)

    def generate_global_supplier_summary(self, filepath: str, balances: list, date_range: str = "All Time"):
        """Generates a summary report of all suppliers/vendors and their outstanding balances"""
        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = self._build_header("Global Supplier Balances Report", date_range)
        
        # Data Table Headers
        data = [["Code", "Vendor Company", "Type", "Total Billed", "Total Paid", "Balance"]]
        
        total_outstanding = 0.0
        total_billed = 0.0
        total_paid = 0.0
        
        for b in balances:
            total_outstanding += b.get('balance', 0)
            total_billed += b.get('billed', 0)
            total_paid += b.get('paid', 0)
            data.append([
                b.get('code', ''),
                b.get('company', ''),
                b.get('type', ''),
                f"Rs. {b.get('billed', 0):,.2f}",
                f"Rs. {b.get('paid', 0):,.2f}",
                f"Rs. {b.get('balance', 0):,.2f}"
            ])
            
        table = Table(data, colWidths=[60, 150, 80, 80, 80, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('GRID', (0,0), (-1,-1), 1, colors.lightgrey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.white])
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        # Calculate cash vs bank breakdown
        total_cash = 0.0
        total_bank = 0.0
        with get_session() as session:
            total_cash = session.scalar(
                select(func.coalesce(func.sum(VendorLedger.debit), 0.0))
                .where(VendorLedger.payment_source == 'Cash')
            ) or 0.0
            total_bank = session.scalar(
                select(func.coalesce(func.sum(VendorLedger.debit), 0.0))
                .where(VendorLedger.payment_source == 'Bank')
            ) or 0.0
        
        # Summary Block
        summary_data = [
            ["Overall Credit (Billed):", f"Rs. {total_billed:,.2f}"],
            ["Overall Debit (Paid):", f"Rs. {total_paid:,.2f}"],
            ["Total Paid via Cash:", f"Rs. {total_cash:,.2f}"],
            ["Total Paid via Bank:", f"Rs. {total_bank:,.2f}"],
            ["Total Market Payables:", f"Rs. {total_outstanding:,.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[150, 150], hAlign='RIGHT')
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0,-1), (-1,-1), colors.HexColor("#1E293B")), # Highlight the final balance
        ]))
        elements.append(summary_table)
        
        doc.build(elements)

from models.quotation import Quotation, QuotationItem
from services.company_profile_service import CompanyProfileService
class QuotationPDFEngine:
    @staticmethod
    def generate_quotation_pdf(filepath: str, quotation_id: str):
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
        from reportlab.lib.utils import ImageReader
        import io
        from datetime import datetime
        
        from config.database import get_session
        from models.quotation import Quotation, QuotationItem
        from services.company_profile_service import CompanyProfileService
        
        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=inch, leftMargin=inch, topMargin=inch, bottomMargin=inch)
        styles = getSampleStyleSheet()
        elements = []
        
        with get_session() as session:
            quotation = session.get(Quotation, quotation_id)
            items = session.query(QuotationItem).filter_by(quotation_id=quotation.id).all()
            
        profile_svc = CompanyProfileService()
        company = profile_svc.get_profile()
        
        if company:
            comp_name = company.company_name or "Travel Agency"
            address = company.address or ""
            phone = company.phone or ""
            email = company.email or ""
            logo_data = company.logo_data
        else:
            comp_name = "Travel Agency"
            address = ""
            phone = ""
            email = ""
            logo_data = None
            
        # --- Header Section ---
        header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=20, leading=24, spaceAfter=8, textColor=colors.HexColor('#1E3A8A'))
        sub_header_style = ParagraphStyle('SubHeaderStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor('#475569'))
        
        header_text = f"<b>{comp_name}</b>"
        sub_header_text = ""
        if address: sub_header_text += f"{address}<br/>"
        if phone: sub_header_text += f"Phone: {phone}<br/>"
        if email: sub_header_text += f"Email: {email}"
        
        if logo_data:
            image_stream = io.BytesIO(logo_data)
            reader = ImageReader(image_stream)
            orig_width, orig_height = reader.getSize()
            max_height = 80
            aspect_ratio = orig_width / float(orig_height)
            logo_w = max_height * aspect_ratio
            logo_h = max_height
            image_stream.seek(0)
            logo_flowable = Image(image_stream, width=logo_w, height=logo_h)
        else:
            logo_flowable = Paragraph("<font size=10 color='#94A3B8'>No Logo</font>", styles['Normal'])

        header_table_data = [
            [logo_flowable, [Paragraph(header_text, header_style), Paragraph(sub_header_text, sub_header_style)]]
        ]
        
        # Max width of A4 with 1 inch margins is 6.27 inches (approx 451 points). 
        # But we'll use exact points or standard inches. Let's use 6.27 inches total = 451.
        header_table = Table(header_table_data, colWidths=[1.5*inch, 4.77*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 0.4 * inch))
        
        # --- Title Section ---
        title_style = ParagraphStyle('TitleCenter', parent=styles['Heading1'], alignment=TA_CENTER, spaceAfter=6, fontName='Helvetica-Bold', textColor=colors.HexColor('#0F172A'))
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], alignment=TA_CENTER, textColor=colors.HexColor('#DC2626'), fontSize=10, spaceAfter=20, fontName='Helvetica-Bold')
        
        elements.append(Paragraph("ESTIMATE / QUOTATION", title_style))
        elements.append(Paragraph("*** This is not a tax invoice ***", subtitle_style))
        elements.append(Spacer(1, 0.1 * inch))
        
        # --- Customer and Quote Info ---
        info_style = ParagraphStyle('InfoStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#334155'))
        
        guest_name = (quotation.guest_name or "Walk-in").upper()
        guest_phone = quotation.guest_phone or "N/A"
        date_str = quotation.date_created.strftime("%d-%b-%Y")
        ref_id = quotation.id[:8].upper()
        
        info_data = [
            [Paragraph(f"<b>Guest Name:</b> {guest_name}", info_style), Paragraph(f"<b>Quote Ref:</b> {ref_id}", info_style)],
            [Paragraph(f"<b>Phone:</b> {guest_phone}", info_style), Paragraph(f"<b>Date:</b> {date_str}", info_style)],
        ]
        
        info_table = Table(info_data, colWidths=[3.13*inch, 3.13*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8)
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # --- Items Table ---
        table_data = [["S.NO", "SERVICE DESCRIPTION", "QTY", "UNIT PRICE", "TOTAL"]]
        
        for i, item in enumerate(items, start=1):
            details_para = Paragraph(item.service_description, styles['Normal'])
            price_str = f"{(item.unit_price or 0):,.2f}"
            total_str = f"{(item.total or 0):,.2f}"
            table_data.append([str(i), details_para, str(item.qty), price_str, total_str])
            
        table_data.append(["", "", "", "G R A N D   T O T A L", f"Rs. {(quotation.total_amount or 0):,.2f}"])
        
        main_table = Table(table_data, colWidths=[35, 235, 45, 90, 100])
        
        row_count = len(table_data)
        grand_row = row_count - 1
        
        table_style = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A1A2E')), # _COLOR_HEADER
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('ALIGN', (1,1), (1, grand_row - 1), 'LEFT'),
            ('ALIGN', (3,1), (4,-1), 'RIGHT'),
            
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            
            # Inner Grid and Borders
            ('GRID', (0,0), (-1, grand_row - 1), 0.5, colors.grey),
            ('BOX', (0,0), (-1, -1), 1, colors.black),
            
            # Grand total row formatting
            ('BACKGROUND', (0, grand_row), (-1, grand_row), colors.HexColor('#1B2631')), # _COLOR_TOTAL
            ('TEXTCOLOR', (0, grand_row), (-1, grand_row), colors.white),
            ('SPAN', (0, grand_row), (2, grand_row)),
            ('ALIGN', (3, grand_row), (3, grand_row), 'RIGHT'),
            ('FONTNAME', (3, grand_row), (4, grand_row), 'Helvetica-Bold'),
            ('BOX', (0, grand_row), (-1, grand_row), 1, colors.black),
            ('INNERGRID', (3, grand_row), (4, grand_row), 1, colors.black),
        ])
        
        # Alternating row colors
        for i in range(1, grand_row):
            if i % 2 == 0:
                table_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F4F6F7'))
                
        main_table.setStyle(table_style)
        elements.append(main_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Amount in words
        try:
            from services.invoice_generator import InvoiceGenerator
            amount_words = InvoiceGenerator._amount_to_words(int(quotation.total_amount or 0))
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

        
        # --- Footer Section ---
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#94A3B8'), spaceAfter=15))
        
        disclaimer_style = ParagraphStyle('DisclaimerStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=colors.HexColor('#64748B'), alignment=TA_CENTER)
        
        disclaimer_text = "<b>Please Note:</b> This is an estimated price based on current availability. Final prices are not fixed and are subject to change without notice until booking is fully confirmed and paid."
        elements.append(Paragraph(disclaimer_text, disclaimer_style))
        
        doc.build(elements)
        return filepath
