from typing import Callable, TYPE_CHECKING
from PySide6.QtCore import QObject, Signal, QThread
import traceback

if TYPE_CHECKING:
    from core.base_model import BaseModel
    User = BaseModel  # Placeholder type hint if User is a BaseModel

class WorkerThread(QThread):
    """Worker thread to run background tasks without blocking the UI."""
    finished_signal = Signal(object)
    error_signal = Signal(str)

    def __init__(self, func: Callable, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(f"{str(e)}\n{traceback.format_exc()}")

class BaseViewModel(QObject):
    """Base View Model class providing common UI state management and signals."""
    
    error_occurred = Signal(str)
    success_occurred = Signal(str)
    loading_changed = Signal(bool)
    data_changed = Signal()

    def __init__(self):
        super().__init__()
        self._is_loading: bool = False
        self._current_user: 'User | None' = None
        self._workers: list[WorkerThread] = []

    @property
    def is_loading(self) -> bool:
        return self._is_loading

    @property
    def current_user(self) -> 'User | None':
        return self._current_user

    @current_user.setter
    def current_user(self, user: 'User | None'):
        self._current_user = user

    def set_loading(self, loading: bool) -> None:
        """Set the loading state and emit a signal."""
        self._is_loading = loading
        self.loading_changed.emit(loading)

    def show_error(self, message: str) -> None:
        """Emit an error signal to be shown in the UI."""
        self.error_occurred.emit(message)

    def show_success(self, message: str) -> None:
        """Emit a success signal to be shown in the UI."""
        self.success_occurred.emit(message)

    def run_in_thread(self, func: Callable, on_success: Callable | None = None, on_error: Callable | None = None, *args, **kwargs) -> None:
        """Run a function in a background worker thread."""
        self.set_loading(True)
        worker = WorkerThread(func, *args, **kwargs)
        self._workers.append(worker)
        
        def handle_success(result):
            self.set_loading(False)
            if on_success:
                on_success(result)
            self._cleanup_worker(worker)
                
        def handle_error(err):
            self.set_loading(False)
            if on_error:
                on_error(err)
            else:
                self.show_error(err)
            self._cleanup_worker(worker)
                
        worker.finished_signal.connect(handle_success)
        worker.error_signal.connect(handle_error)
        worker.finished.connect(worker.deleteLater)
        worker.start()

    def _cleanup_worker(self, worker: WorkerThread):
        if worker in self._workers:
            self._workers.remove(worker)
