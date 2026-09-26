import os
from config.database import get_session, _run_migrations, _create_tables_directly

# 1. First ensure the models are defined
# We already wrote models/quotation.py and modified models/__init__.py
print("Creating tables directly to ensure quotations table exists...")
_create_tables_directly()

# 2. Add Quotation service methods
service_file = "services/accounting_service.py"
with open(service_file, "r") as f:
    content = f.read()

if "get_quotations(" not in content:
    with open(service_file, "a") as f:
        f.write("\n")
        f.write("    def search_quotations(self, query: str = \"\", skip: int = 0, limit: int = 50) -> dict:\n")
        f.write("        from models.quotation import Quotation\n")
        f.write("        from sqlalchemy import or_\n")
        f.write("        with self._get_session() as session:\n")
        f.write("            q = session.query(Quotation)\n")
        f.write("            if query:\n")
        f.write("                q = q.filter(or_(Quotation.guest_name.ilike(f'%{query}%'), Quotation.id.ilike(f'%{query}%')))\n")
        f.write("            total = q.count()\n")
        f.write("            items = q.order_by(Quotation.created_at.desc()).offset(skip).limit(limit).all()\n")
        f.write("            return {'total': total, 'items': items}\n")

# 3. Add to ViewModel
vm_file = "viewmodels/accounting_viewmodel.py"
with open(vm_file, "r") as f:
    content = f.read()

if "quotations_loaded" not in content:
    content = content.replace("invoices_loaded = Signal(list, int)", "invoices_loaded = Signal(list, int)\n    quotations_loaded = Signal(list, int)")
    
    with open(vm_file, "w") as f:
        f.write(content)
        
    with open(vm_file, "a") as f:
        f.write("\n")
        f.write("    def load_quotations(self, query: str = \"\", skip: int = 0, limit: int = 50):\n")
        f.write("        self.set_loading(True)\n")
        f.write("        self.run_in_thread(\n")
        f.write("            lambda: self._service.search_quotations(query, skip, limit),\n")
        f.write("            on_success=lambda res: self._on_quotations_success(res),\n")
        f.write("            on_error=self.show_error\n")
        f.write("        )\n")
        f.write("    def _on_quotations_success(self, result):\n")
        f.write("        self.set_loading(False)\n")
        f.write("        self.quotations_loaded.emit(result['items'], result['total'])\n")

# 4. Modify Accounts Page to fully replace Invoices with Quotations
accounts_file = "ui/pages/accounting/accounts_page.py"
with open(accounts_file, "r", encoding="utf-8") as f:
    accounts = f.read()

# Tab renaming
accounts = accounts.replace('self.tabs.addTab(tab_inv, "Invoices")', 'self.tabs.addTab(tab_inv, "Quotations")')
accounts = accounts.replace('self.tbl_inv = self._create_table(["Invoice #", "Date", "Customer", "Subtotal", "Tax", "Total", "Paid", "Balance", "Status", "Actions"])', 'self.tbl_inv = self._create_table(["Quote #", "Date", "Guest Name", "Phone", "Total Amount", "Status", "Actions"])')

accounts = accounts.replace('self.viewmodel.invoices_loaded.connect(self._on_invoices_loaded)', 'self.viewmodel.quotations_loaded.connect(self._on_quotations_loaded)')

# Replace _on_invoices_loaded with _on_quotations_loaded
import re
invoices_loaded_pattern = r'    def _on_invoices_loaded\(self, invoices, total\):.*?        self.lbl_inv_page\.setText\(f"Page {self\.inv_page} of {max\(1, total_pages\)}"\)'
replacement = """    def _on_quotations_loaded(self, quotations, total):
        self.tbl_inv.setRowCount(0)
        from PySide6.QtWidgets import QPushButton, QTableWidgetItem
        from utils.formatters import format_currency, format_date
        
        self.total_inv = total
        for row, q in enumerate(quotations):
            self.tbl_inv.insertRow(row)
            self.tbl_inv.setItem(row, 0, QTableWidgetItem(q.id[:8].upper()))
            self.tbl_inv.setItem(row, 1, QTableWidgetItem(format_date(q.date_created)))
            self.tbl_inv.setItem(row, 2, QTableWidgetItem(q.guest_name or 'Walk-in'))
            self.tbl_inv.setItem(row, 3, QTableWidgetItem(q.guest_phone or '-'))
            self.tbl_inv.setItem(row, 4, QTableWidgetItem(format_currency(q.total_amount)))
            self.tbl_inv.setItem(row, 5, QTableWidgetItem(q.status))
            
            btn_print = QPushButton("Print")
            btn_print.setStyleSheet("background-color: #3b82f6; color: white;")
            btn_print.clicked.connect(lambda checked=False, q_id=q.id, g_name=q.guest_name: self._print_quotation(q_id, g_name))
            self.tbl_inv.setCellWidget(row, 6, btn_print)
            
        import math
        total_pages = math.ceil(total / self.page_size)
        self.lbl_inv_page.setText(f"Page {self.inv_page} of {max(1, total_pages)}")"""

accounts = re.sub(invoices_loaded_pattern, replacement, accounts, flags=re.DOTALL)

# Modify refresh to load quotations
accounts = accounts.replace('self.viewmodel.load_invoices(self.inv_search.text(), skip=(self.inv_page-1)*self.page_size, limit=self.page_size)', 'self.viewmodel.load_quotations(self.inv_search.text(), skip=(self.inv_page-1)*self.page_size, limit=self.page_size)')

# Add print logic
print_logic = """
    def _print_quotation(self, quotation_id, guest_name):
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        from services.pdf_engine import QuotationPDFEngine
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Quotation PDF",
            f"Quotation_{guest_name or 'Walk-in'}.pdf",
            "PDF Files (*.pdf)"
        )
        
        if filepath:
            try:
                QuotationPDFEngine.generate_quotation_pdf(filepath, quotation_id)
                QMessageBox.information(self, "Success", "Quotation PDF generated successfully!")
                QDesktopServices.openUrl(QUrl.fromLocalFile(filepath))
            except Exception as e:
                import logging
                logging.exception("Failed to generate PDF")
                QMessageBox.critical(self, "Error", f"Failed to generate PDF: {str(e)}")
"""
accounts += print_logic

with open(accounts_file, "w", encoding="utf-8") as f:
    f.write(accounts)

# Add QuotationPDFEngine to services/pdf_engine.py
pdf_file = "services/pdf_engine.py"
with open(pdf_file, "r") as f:
    pdf_content = f.read()

if "class QuotationPDFEngine:" not in pdf_content:
    with open(pdf_file, "a") as f:
        f.write("\n")
        f.write("from models.quotation import Quotation, QuotationItem\n")
        f.write("from services.company_profile_service import CompanyProfileService\n")
        f.write("class QuotationPDFEngine:\n")
        f.write("    @staticmethod\n")
        f.write("    def generate_quotation_pdf(filepath: str, quotation_id: str):\n")
        f.write("        from reportlab.lib.pagesizes import A4\n")
        f.write("        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle\n")
        f.write("        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle\n")
        f.write("        from reportlab.lib import colors\n")
        f.write("        from reportlab.lib.units import inch\n")
        f.write("        from config.database import get_session\n")
        f.write("        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=inch, leftMargin=inch, topMargin=inch, bottomMargin=inch)\n")
        f.write("        styles = getSampleStyleSheet()\n")
        f.write("        title_style = ParagraphStyle('TitleCenter', parent=styles['Heading1'], alignment=1, spaceAfter=6)\n")
        f.write("        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], alignment=1, textColor=colors.red, fontSize=10, spaceAfter=20)\n")
        f.write("        bold_normal = ParagraphStyle('BoldNormal', parent=styles['Normal'], fontName='Helvetica-Bold')\n")
        f.write("        normal_style = styles['Normal']\n")
        f.write("        with get_session() as session:\n")
        f.write("            quotation = session.get(Quotation, quotation_id)\n")
        f.write("            items = session.query(QuotationItem).filter_by(quotation_id=quotation.id).all()\n")
        f.write("        profile_svc = CompanyProfileService()\n")
        f.write("        company = profile_svc.get_profile()\n")
        f.write("        company_name = company.company_name if company else \"Travel Agency\"\n")
        f.write("        story = []\n")
        f.write("        story.append(Paragraph(company_name, title_style))\n")
        f.write("        story.append(Paragraph(\"ESTIMATE / QUOTATION\", title_style))\n")
        f.write("        story.append(Paragraph(\"<b>*** This is not a tax invoice ***</b>\", subtitle_style))\n")
        f.write("        details_data = [\n")
        f.write("            [Paragraph(f\"<b>Quote Ref:</b> {quotation.id[:8].upper()}\", normal_style), Paragraph(f\"<b>Guest Name:</b> {quotation.guest_name or 'Walk-in'}\", normal_style)],\n")
        f.write("            [Paragraph(f\"<b>Date:</b> {quotation.date_created.strftime('%d-%b-%Y')}\", normal_style), Paragraph(f\"<b>Guest Phone:</b> {quotation.guest_phone or 'N/A'}\", normal_style)],\n")
        f.write("            [Paragraph(f\"<b>Valid Until:</b> {quotation.valid_until.strftime('%d-%b-%Y')}\", bold_normal), \"\"]\n")
        f.write("        ]\n")
        f.write("        details_table = Table(details_data, colWidths=[3.25*inch, 3.25*inch])\n")
        f.write("        details_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 8)]))\n")
        f.write("        story.append(details_table)\n")
        f.write("        story.append(Spacer(1, 0.25 * inch))\n")
        f.write("        table_data = [[\"Service Description\", \"Qty\", \"Unit Price\", \"Total\"]]\n")
        f.write("        for item in items:\n")
        f.write("            table_data.append([item.service_description, str(item.qty), f\"Rs. {item.unit_price:,.2f}\", f\"Rs. {item.total:,.2f}\"])\n")
        f.write("        table_data.append([\"\", \"\", \"Grand Total:\", f\"Rs. {quotation.total_amount:,.2f}\"])\n")
        f.write("        t = Table(table_data, colWidths=[3.5*inch, 0.75*inch, 1.1*inch, 1.15*inch])\n")
        f.write("        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563EB')), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('ALIGN', (0,0), (-1,-1), 'LEFT'), ('ALIGN', (1,0), (-1,-1), 'RIGHT'), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('BOTTOMPADDING', (0,0), (-1,0), 12), ('TOPPADDING', (0,0), (-1,0), 12), ('BACKGROUND', (0,1), (-1,-2), colors.HexColor('#F8FAFC')), ('GRID', (0,0), (-1,-2), 1, colors.HexColor('#E2E8F0')), ('FONTNAME', (2,-1), (3,-1), 'Helvetica-Bold'), ('TEXTCOLOR', (2,-1), (3,-1), colors.HexColor('#10B981')), ('TOPPADDING', (2,-1), (3,-1), 12), ('LINEABOVE', (2,-1), (3,-1), 2, colors.HexColor('#2563EB'))]))\n")
        f.write("        story.append(t)\n")
        f.write("        story.append(Spacer(1, 0.75 * inch))\n")
        f.write("        story.append(Paragraph(f\"Thank you for your inquiry. Prices subject to change after {quotation.valid_until.strftime('%d-%b-%Y')}.\", normal_style))\n")
        f.write("        doc.build(story)\n")
        f.write("        return filepath\n")

print("Done")
