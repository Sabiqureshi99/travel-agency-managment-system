import sys
import traceback
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env", override=False)

def main():
    try:
        from config.database import init_database
        init_database()
        
        from PySide6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        
        from ui.pages.umrah.umrah_list import UmrahListPage
        from models.user import User
        u = User(id='test')
        w = UmrahListPage(u)
        
        # force loading to happen
        app.processEvents()
        
        print('success')
    except Exception as e:
        print("ERROR OCCURRED:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
