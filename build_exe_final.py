import os
import subprocess
import sys
import shutil

def build_exe():
    print("Starting PyInstaller build process...")
    
    # Clean previous build
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
        
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name", "TAMS_ERP",
        "--windowed",            # Don't show console window
        "--noconfirm",           # Overwrite output directory without asking
        "--add-data", f"ui{os.pathsep}ui", 
        "--add-data", f"alembic.ini{os.pathsep}.",
        "--add-data", f"alembic{os.pathsep}alembic",
        "--add-data", f".env{os.pathsep}.",
        "--hidden-import", "alembic",
        "--hidden-import", "sqlite3",
        "--hidden-import", "PySide6.QtSql",
        "--hidden-import", "reportlab",
        "--hidden-import", "pytesseract",
        "main.py"
    ]
    
    print("Running command:", " ".join(cmd))
    
    # Run the command
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Build Successful! Executable is located in the 'dist' folder.")
    else:
        print("Build Failed.")
        print(result.stdout)
        print(result.stderr)

if __name__ == "__main__":
    build_exe()
