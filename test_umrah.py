import sys
from PySide6.QtWidgets import QApplication
import traceback

def main():
    try:
        app = QApplication(sys.argv)
        from ui.pages.umrah.umrah_list import UmrahListPage
        from models.user import User
        u = User(id='test')
        w = UmrahListPage(u)
        print('Instantiated successfully')
    except Exception as e:
        traceback.print_exc()

if __name__ == "__main__":
    main()
