import os
import subprocess
import sys
import shutil

def build():
    print("Starting final production build...")
    
    dist_dir = "dist_final"
    build_dir = "build_final"
    
    if os.path.exists(build_dir):
        try:
            shutil.rmtree(build_dir)
        except Exception as e:
            print(f"Warning: could not delete {build_dir}: {e}")
            
    if os.path.exists(dist_dir):
        try:
            shutil.rmtree(dist_dir)
        except Exception as e:
            print(f"Warning: could not delete {dist_dir}: {e}")
            
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name", "TAMS_ERP",
        "--windowed",
        "--noconfirm",
        "--distpath", dist_dir,
        "--workpath", build_dir,
        "--add-data", f"alembic.ini{os.pathsep}.",
        "--add-data", f"alembic{os.pathsep}alembic",
    ]
    
    if os.path.exists(".env"):
        cmd.extend(["--add-data", f".env{os.pathsep}."])
    
    if os.path.exists("logo"):
        cmd.extend(["--add-data", f"logo{os.pathsep}logo"])
    if os.path.exists("ui"):
        cmd.extend(["--add-data", f"ui{os.pathsep}ui"])
        
    hidden_imports = [
        "alembic", "sqlite3", "PySide6.QtSql", "reportlab", "pytesseract",
        "bcrypt", "sqlalchemy.ext.baked", "psycopg2"
    ]
    
    for hi in hidden_imports:
        cmd.extend(["--hidden-import", hi])
        
    cmd.append("main.py")
    
    print("Running PyInstaller...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"Build Successful! Output in '{dist_dir}\\TAMS_ERP'")
    else:
        print("Build Failed.")
        print(result.stderr[-2000:])
        sys.exit(1)

if __name__ == "__main__":
    build()
