from PySide6.QtCore import Signal
from services.report_service import ReportService
from core.base_viewmodel import BaseViewModel
import csv

class ReportsViewModel(BaseViewModel):
    report_generated = Signal(dict)
    export_completed = Signal(str)
    export_failed = Signal(str)

    def __init__(self):
        super().__init__()
        self.report_service = ReportService()
        self.current_report = None

    def generate_report(self, start_date, end_date):
        def _generate():
            self.current_report = self.report_service.generate_financial_report(start_date, end_date)
            return self.current_report
        self.run_in_thread(_generate, self.report_generated.emit)

    def export_to_csv(self, filepath):
        if not self.current_report:
            self.export_failed.emit("No report generated to export.")
            return
            
        def _export():
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Type", "Reference", "Description", "Amount"])
                for item in self.current_report.get('items', []):
                    writer.writerow([
                        item['date'],
                        item['type'],
                        item['reference'],
                        item['description'],
                        f"{item['amount']:.2f}"
                    ])
            return filepath
            
        self.run_in_thread(_export, self.export_completed.emit, on_error=lambda e: self.export_failed.emit(str(e)))
