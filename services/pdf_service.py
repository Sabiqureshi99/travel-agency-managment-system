from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib import colors
import os

class PDFService:
    def __init__(self, output_dir="output/pdfs"):
        self.output_dir = output_dir
        # Ensure the output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(name='RightAlign', alignment=2))
        
    def _build_company_header_table(self):
        import io
        from reportlab.platypus import Table, TableStyle, Image as RLImage, Paragraph
        from config.database import get_session
        from models.company_profile import CompanyProfile
        
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
                        img_stream = io.BytesIO(profile.logo_data)
                        reader = ImageReader(img_stream)
                        orig_width, orig_height = reader.getSize()
                        max_height = 60
                        aspect_ratio = orig_width / float(orig_height)
                        logo_w = max_height * aspect_ratio
                        
                        img_stream.seek(0)
                        logo_img = RLImage(img_stream, width=logo_w, height=max_height)
                        logo_img.hAlign = 'LEFT'
                    except Exception:
                        pass
        
        if not logo_img:
            logo_path = os.path.abspath("logo/logo.png")
            if os.path.exists(logo_path):
                try:
                    from reportlab.lib.utils import ImageReader
                    reader = ImageReader(logo_path)
                    orig_width, orig_height = reader.getSize()
                    max_height = 60
                    aspect_ratio = orig_width / float(orig_height)
                    logo_w = max_height * aspect_ratio
                    
                    logo_img = RLImage(logo_path, width=logo_w, height=max_height)
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
        return header_table

    def generate_group_invoice(self, invoice, booking, pax_list):
        filename = os.path.join(self.output_dir, f"Invoice_{invoice.invoice_number}.pdf")
        doc = SimpleDocTemplate(filename, pagesize=A4)
        from typing import Any
        from reportlab.platypus.flowables import Flowable
        elements: list[Flowable] = []
        
        # Header
        elements.append(self._build_company_header_table())
        
        elements.append(Paragraph(f"Invoice #: {invoice.invoice_number}", self.styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Customer Info (Group Leader)
        elements.append(Paragraph(f"<b>Billed To:</b> Customer ID {invoice.customer_id}", self.styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # PAX / Line Items Table
        data = [["PAX Name", "Passport", "Service Detail", "Amount"]]
        
        for pax in pax_list:
            data.append([
                f"{pax.first_name} {pax.last_name}",
                pax.passport_number or "N/A",
                "Unified Booking Package",
                f"{booking.selling_price / max(len(pax_list), 1):.2f}" # Split equally for display
            ])
            
        table = Table(data, colWidths=[120, 100, 180, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 30))
        
        # Total
        elements.append(Paragraph(f"<b>Total Amount:</b> {invoice.total_amount}", self.styles['Heading3']))
        
        doc.build(elements)
        return filename

    def generate_customer_statement(self, customer, statement_entries, balance_due):
        filename = os.path.join(self.output_dir, f"Statement_{customer.id}.pdf")
        doc = SimpleDocTemplate(filename, pagesize=A4, 
                                rightMargin=40, leftMargin=40, 
                                topMargin=40, bottomMargin=40)
        from typing import Any
        from reportlab.platypus.flowables import Flowable
        elements: list[Flowable] = []
        
        # Header
        elements.append(self._build_company_header_table())
        elements.append(Spacer(1, 15))
        
        # Horizontal Line
        from reportlab.graphics.shapes import Drawing, Line
        d = Drawing(515, 1)
        d.add(Line(0, 0, 515, 0))
        elements.append(d)
        elements.append(Spacer(1, 15))
        
        # Title & Customer Details
        elements.append(Paragraph(f"<b>ACCOUNT STATEMENT</b>", self.styles['Title']))
        elements.append(Spacer(1, 15))
        
        cust_info = f"<b>Customer Name:</b> {customer.first_name} {customer.last_name}<br/>"
        if hasattr(customer, 'customer_code') and customer.customer_code:
            cust_info += f"<b>Customer Code:</b> {customer.customer_code}<br/>"
        if hasattr(customer, 'phone_primary') and customer.phone_primary:
            cust_info += f"<b>Phone:</b> {customer.phone_primary}<br/>"
            
        elements.append(Paragraph(cust_info, self.styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Ledger Table
        data = [["Date", "Reference", "Debit (Inv)", "Credit (Receipt)", "Balance"]]
        running_balance = 0
        
        for entry in statement_entries:
            debit = entry.get('debit', 0)
            credit = entry.get('credit', 0)
            running_balance += (debit - credit)
            
            data.append([
                entry['date'].strftime('%Y-%m-%d'),
                entry['reference'],
                f"{debit:,.2f}" if debit else "-",
                f"{credit:,.2f}" if credit else "-",
                f"{running_balance:,.2f}"
            ])
            
        table = Table(data, colWidths=[90, 125, 100, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563EB')), # A nice blue
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 10),
            ('TOPPADDING', (0,0), (-1,0), 10),
            
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
            ('TEXTCOLOR', (0,1), (-1,-1), colors.black),
            ('ALIGN', (2,1), (-1,-1), 'RIGHT'), # Align amounts right
            ('ALIGN', (0,1), (1,-1), 'LEFT'), # Align date and ref left
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#E5E7EB')), # Light gray border
            ('BOTTOMPADDING', (0,1), (-1,-1), 6),
            ('TOPPADDING', (0,1), (-1,-1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]), # Alternating rows
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        # Final Balance summary
        summary_data = [
            ["", "Total Outstanding Balance:", f"PKR {balance_due:,.2f}"]
        ]
        
        sum_table = Table(summary_data, colWidths=[215, 200, 100])
        sum_table.setStyle(TableStyle([
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('ALIGN', (2,0), (2,0), 'RIGHT'),
            ('FONTNAME', (1,0), (-1,-1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (2,0), (2,0), colors.HexColor('#DC2626') if balance_due > 0 else colors.HexColor('#059669')),
            ('SIZE', (1,0), (-1,-1), 12),
        ]))
        elements.append(sum_table)
        
        # Footer
        elements.append(Spacer(1, 40))
        elements.append(Paragraph("<i>This is a computer generated document and does not require a physical signature.</i>", self.styles['Normal']))
        
        doc.build(elements)
        return filename

    def generate_vendor_ledger_pdf(self, vendor, entries, balance, start_date=None, end_date=None):
        filename = os.path.join(self.output_dir, f"Vendor_Ledger_{vendor.vendor_code}.pdf")
        doc = SimpleDocTemplate(filename, pagesize=A4)
        from typing import Any
        from reportlab.platypus.flowables import Flowable
        elements: list[Flowable] = []
        
        # Header
        elements.append(self._build_company_header_table())
        elements.append(Paragraph(f"<b>Vendor Ledger Statement</b>", self.styles['Title']))
        elements.append(Paragraph(f"Vendor: {vendor.company_name} ({vendor.vendor_type})", self.styles['Heading2']))
        if start_date and end_date:
            elements.append(Paragraph(f"Period: {start_date} to {end_date}", self.styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Ledger Table
        data = [["Date", "Description", "Ref Booking", "Debit (Paid)", "Credit (Billed)", "Balance"]]
        running_balance = 0
        
        for entry in entries:
            debit = entry.get('debit', 0)
            credit = entry.get('credit', 0)
            running_balance += (credit - debit)
            
            data.append([
                entry['date'].strftime('%Y-%m-%d') if hasattr(entry['date'], 'strftime') else entry['date'],
                entry['description'],
                entry['reference'],
                f"{debit:.2f}" if debit else "-",
                f"{credit:.2f}" if credit else "-",
                f"{running_balance:.2f}"
            ])
            
        table = Table(data, colWidths=[60, 150, 80, 80, 80, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('ALIGN', (3,1), (-1,-1), 'RIGHT'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        # Final Balance
        elements.append(Paragraph(f"<b>Closing Balance:</b> PKR {balance:.2f}", self.styles['Heading3']))
        
        doc.build(elements)
        return filename

    def generate_financial_report(self, data, start_date, end_date):
        filename = os.path.join(self.output_dir, f"Financial_Report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf")
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        from typing import Any
        from reportlab.platypus.flowables import Flowable
        
        elements: list[Flowable] = []
        
        # Header - Professional Style with Logo
        elements.append(self._build_company_header_table())
        
        from reportlab.graphics.shapes import Drawing, Line
        from reportlab.graphics.charts.piecharts import Pie
        from reportlab.lib.units import inch
        
        d = Drawing(515, 1)
        d.add(Line(0, 0, 515, 0))
        elements.append(d)
        elements.append(Spacer(1, 15))
        
        # Title
        elements.append(Paragraph("<b>COMPREHENSIVE FINANCIAL REPORT</b>", self.styles['Title']))
        elements.append(Paragraph(f"<b>Period:</b> {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}", self.styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # --- 1. FINANCIAL SUMMARY ---
        elements.append(Paragraph("<b>1. Financial Performance Summary</b>", self.styles['Heading2']))
        
        gross_rev = data.get('gross_revenue', 0.0)
        gross_prof = data.get('gross_profit', 0.0)
        net_prof = data.get('net_profit', 0.0)
        gross_margin = (gross_prof / gross_rev * 100) if gross_rev else 0.0
        net_margin = (net_prof / gross_rev * 100) if gross_rev else 0.0
        
        summary_data = [
            ["Gross Revenue:", f"PKR {gross_rev:,.2f}"],
            ["Cost of Services (COGS):", f"PKR {data.get('cogs', 0.0):,.2f}"],
            ["Gross Profit:", f"PKR {gross_prof:,.2f}"],
            ["Operating Expenses:", f"PKR {data.get('total_expenses', 0.0):,.2f}"],
            ["Net Profit:", f"PKR {net_prof:,.2f}"],
            ["Gross Margin %:", f"{gross_margin:.1f}%"],
            ["Net Margin %:", f"{net_margin:.1f}%"]
        ]
        
        t_summary = Table(summary_data, colWidths=[200, 150])
        t_summary.setStyle(TableStyle([
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('FONTNAME', (0,4), (1,4), 'Helvetica-Bold'), # Bold Net Profit
            ('LINEABOVE', (0,4), (1,4), 1, colors.black),
            ('TEXTCOLOR', (1,4), (1,4), colors.HexColor('#059669') if net_prof > 0 else colors.HexColor('#DC2626')),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(t_summary)
        elements.append(Spacer(1, 20))
        
        # --- 2. RECEIVABLES & PAYABLES ---
        elements.append(Paragraph("<b>2. Receivables & Payables (Outstanding)</b>", self.styles['Heading2']))
        
        ar_ap_data = [
            ["Accounts Receivable (Customer Dues):", f"PKR {data.get('customer_dues', 0.0):,.2f}"],
            ["Profits Stuck in Dues (Unrealized):", f"PKR {data.get('stuck_profit', 0.0):,.2f}"],
            ["Total Vendor Bills (Purchases):", f"PKR {data.get('total_vendor_bills', 0.0):,.2f}"],
            ["Total Vendor Payments Made:", f"PKR {data.get('total_vendor_payments', 0.0):,.2f}"],
            ["Accounts Payable (Outstanding Debt):", f"PKR {data.get('total_outstanding_debt', 0.0):,.2f}"]
        ]
        
        t_arap = Table(ar_ap_data, colWidths=[250, 150])
        t_arap.setStyle(TableStyle([
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('FONTNAME', (0,4), (1,4), 'Helvetica-Bold'), 
            ('TEXTCOLOR', (1,4), (1,4), colors.HexColor('#DC2626')), # Debt is red
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(t_arap)
        elements.append(Spacer(1, 20))
        
        # --- 3. BOOKING VOLUME & PROFITABILITY ---
        elements.append(Paragraph("<b>3. Booking Volume & Profitability</b>", self.styles['Heading2']))
        bp = data.get('booking_profits', [])
        if bp:
            bp_table_data: list[list[Any]] = [["Booking Type", "Volume", "Revenue", "Net Profit"]]
            for b in bp:
                bp_table_data.append([
                    b['booking_type'],
                    str(b['volume']),
                    f"{b['revenue']:,.2f}",
                    f"{b['profit']:,.2f}"
                ])
            t_bp = Table(bp_table_data, colWidths=[150, 80, 100, 100])
            t_bp.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563EB')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
                ('ALIGN', (0,0), (0,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#E5E7EB')),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ]))
            elements.append(t_bp)
        else:
            elements.append(Paragraph("No booking data available for this period.", self.styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # --- 4. RECEIVABLES AGING ---
        elements.append(Paragraph("<b>4. Receivables Aging Summary (Top 5)</b>", self.styles['Heading2']))
        aging = data.get('receivables_aging', [])
        if aging:
            aging_table_data: list[list[Any]] = [["Customer Name", "Total Owed", "0-30 Days", "31-60 Days", "60+ Days"]]
            for a in aging[:5]: # Top 5
                aging_table_data.append([
                    a['customer_name'][:25] + "..." if len(a['customer_name']) > 25 else a['customer_name'],
                    f"{a['total_outstanding']:,.0f}",
                    f"{a['0_30_days']:,.0f}",
                    f"{a['31_60_days']:,.0f}",
                    f"{a['60_plus_days']:,.0f}"
                ])
            t_aging = Table(aging_table_data, colWidths=[130, 80, 80, 80, 80])
            t_aging.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4B5563')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#E5E7EB')),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('TEXTCOLOR', (4,1), (4,-1), colors.HexColor('#DC2626')), # 60+ days in red
            ]))
            elements.append(t_aging)
        else:
            elements.append(Paragraph("No outstanding customer receivables.", self.styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # --- 5. ITEMIZED EXPENSES ---
        elements.append(Paragraph("<b>5. Itemized Expenses Breakdown</b>", self.styles['Heading2']))
        expenses = data.get('itemized_expenses', [])
        if expenses:
            exp_table_data: list[list[Any]] = [["Expense Account", "Amount"]]
            # Add Pie Chart
            drawing = Drawing(400, 200)
            pie = Pie()
            pie.x = 100
            pie.y = 20
            pie.width = 150
            pie.height = 150
            pie.data = [e['amount'] for e in expenses]
            pie.labels = [e['account'][:10] for e in expenses]
            pie.sideLabels = 1
            drawing.add(pie)
            elements.append(drawing)
            elements.append(Spacer(1, 10))
            
            for e in expenses:
                exp_table_data.append([e['account'], f"PKR {e['amount']:,.2f}"])
            t_exp = Table(exp_table_data, colWidths=[200, 150])
            t_exp.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563EB')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (1,0), (1,-1), 'RIGHT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#E5E7EB')),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ]))
            elements.append(t_exp)
        else:
            elements.append(Paragraph("No expenses recorded for this period.", self.styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # --- 6. CASH FLOW LOG ---
        elements.append(Paragraph("<b>6. Cash Flow Log</b>", self.styles['Heading2']))
        
        # In report_service, the key was updated to 'receipts_log'
        all_receipts = data.get('receipts_log', [])
        
        cash_entries = [e for e in all_receipts if e.get('payment_method') == 'Cash']
        if cash_entries:
            trans_table = [["Date", "Ref", "Party", "Type", "Amount"]]
            total_in = 0.0
            total_out = 0.0
            
            for r in cash_entries:
                amt = r['amount']
                if r['type'] == 'IN': total_in += amt
                else: total_out += amt
                
                trans_table.append([
                    r['date'][:10],
                    r['receipt_number'],
                    r['customer'][:25] + "..." if len(r['customer']) > 25 else r['customer'],
                    r['type'],
                    f"{amt:,.2f}"
                ])
                
            t_trans = Table(trans_table, colWidths=[70, 80, 190, 50, 125])
            t_trans.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F2937')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (4,0), (4,-1), 'RIGHT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#E5E7EB')),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ]))
            
            for i, r in enumerate(cash_entries, 1):
                color = colors.HexColor('#059669') if r['type'] == 'IN' else colors.HexColor('#DC2626')
                t_trans.setStyle(TableStyle([('TEXTCOLOR', (3,i), (3,i), color)]))
                t_trans.setStyle(TableStyle([('TEXTCOLOR', (4,i), (4,i), color)]))
                    
            elements.append(t_trans)
            
            net_cash = total_in - total_out
            net_color = '#059669' if net_cash >= 0 else '#DC2626'
            
            summary_html = (
                f"<b>Total IN:</b> <font color='#059669'>Rs. {total_in:,.2f}</font> &nbsp; | &nbsp; "
                f"<b>Total OUT:</b> <font color='#DC2626'>Rs. {total_out:,.2f}</font> &nbsp; | &nbsp; "
                f"<b>Net Cash:</b> <font color='{net_color}'>Rs. {net_cash:,.2f}</font>"
            )
            elements.append(Spacer(1, 5))
            elements.append(Paragraph(summary_html, self.styles['RightAlign']))
        else:
            elements.append(Paragraph("No cash transactions recorded for this period.", self.styles['Normal']))
            
        elements.append(Spacer(1, 20))
        
        # --- 7. BANK FLOW LOG ---
        elements.append(Paragraph("<b>7. Bank Flow Log</b>", self.styles['Heading2']))
        
        bank_entries = [e for e in all_receipts if e.get('payment_method') == 'Bank']
        if bank_entries:
            trans_table = [["Date", "Ref", "Party", "Type", "Amount"]]
            total_in = 0.0
            total_out = 0.0
            
            for r in bank_entries:
                amt = r['amount']
                if r['type'] == 'IN': total_in += amt
                else: total_out += amt
                
                trans_table.append([
                    r['date'][:10],
                    r['receipt_number'],
                    r['customer'][:25] + "..." if len(r['customer']) > 25 else r['customer'],
                    r['type'],
                    f"{amt:,.2f}"
                ])
                
            t_trans = Table(trans_table, colWidths=[70, 80, 190, 50, 125])
            t_trans.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F2937')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (4,0), (4,-1), 'RIGHT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#E5E7EB')),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ]))
            
            for i, r in enumerate(bank_entries, 1):
                color = colors.HexColor('#059669') if r['type'] == 'IN' else colors.HexColor('#DC2626')
                t_trans.setStyle(TableStyle([('TEXTCOLOR', (3,i), (3,i), color)]))
                t_trans.setStyle(TableStyle([('TEXTCOLOR', (4,i), (4,i), color)]))
                    
            elements.append(t_trans)
            
            net_bank = total_in - total_out
            net_color = '#059669' if net_bank >= 0 else '#DC2626'
            
            summary_html = (
                f"<b>Total IN:</b> <font color='#059669'>Rs. {total_in:,.2f}</font> &nbsp; | &nbsp; "
                f"<b>Total OUT:</b> <font color='#DC2626'>Rs. {total_out:,.2f}</font> &nbsp; | &nbsp; "
                f"<b>Net Bank:</b> <font color='{net_color}'>Rs. {net_bank:,.2f}</font>"
            )
            elements.append(Spacer(1, 5))
            elements.append(Paragraph(summary_html, self.styles['RightAlign']))
        else:
            elements.append(Paragraph("No bank transactions recorded for this period.", self.styles['Normal']))

        doc.build(elements)
        return filename
