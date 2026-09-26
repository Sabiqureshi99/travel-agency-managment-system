from PySide6.QtCore import Signal
from core.base_viewmodel import BaseViewModel
from services.dashboard_service import DashboardService

class DashboardViewModel(BaseViewModel):
    """
    ViewModel for the Dashboard Page.
    Fetches high-level statistics and activity from DashboardService.
    """
    
    kpis_updated = Signal(dict)
    recent_activity_updated = Signal(list)
    
    def __init__(self):
        super().__init__()
        self._service = DashboardService()
        
    def load_dashboard_data(self):
        """Load all data required for the dashboard."""
        self.set_loading(True)
        self.run_in_thread(
            self._fetch_data,
            on_success=self._on_fetch_success,
            on_error=self._on_fetch_error
        )
        
    def _fetch_data(self):
        """Run in background thread."""
        kpis = self._service.get_kpis()
        recent_activity = self._service.get_recent_activity(limit=10)
        
        return {
            "kpis": kpis,
            "recent_activity": recent_activity
        }
        
    def _on_fetch_success(self, result):
        self.set_loading(False)
        self.kpis_updated.emit(result["kpis"])
        self.recent_activity_updated.emit(result["recent_activity"])
        
    def _on_fetch_error(self, error):
        self.set_loading(False)
        self.show_error(f"Failed to load dashboard data: {error}")
