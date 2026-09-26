import sys
import traceback
from PySide6.QtWidgets import QApplication

def main():
    app = QApplication(sys.argv)
    try:
        from ui.components.passport_scanner import ScannerDialog
        s = ScannerDialog()
        s.show()
        print('Successfully showed ScannerDialog')
    except Exception as e:
        print('Error:')
        traceback.print_exc()

if __name__ == "__main__":
    main()
