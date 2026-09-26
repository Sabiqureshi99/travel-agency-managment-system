import os
import shutil
import mimetypes
import re
from pathlib import Path

def get_project_root() -> Path:
    """Get the absolute path to the project root directory."""
    return Path(__file__).resolve().parent.parent

def ensure_dir(path: str | Path) -> Path:
    """Ensures a directory exists, creating it if necessary."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

def get_documents_dir() -> Path:
    """Get the documents storage directory."""
    return ensure_dir(get_project_root() / "documents")

def get_photos_dir() -> Path:
    """Get the photos storage directory."""
    return ensure_dir(get_project_root() / "photos")

def get_temp_dir() -> Path:
    """Get the temporary storage directory."""
    return ensure_dir(get_project_root() / "temp")

def get_reports_dir() -> Path:
    """Get the reports storage directory."""
    return ensure_dir(get_project_root() / "reports")

def save_document(source_path: str | Path, category: str, original_filename: str) -> str:
    """Copies a file to the documents directory under a category folder."""
    cat_dir = ensure_dir(get_documents_dir() / category)
    dest_path = cat_dir / sanitize_filename(original_filename)
    shutil.copy2(source_path, dest_path)
    return str(dest_path.relative_to(get_project_root()))

def get_absolute_path(relative_path: str) -> Path:
    """Converts a relative project path to an absolute path."""
    return get_project_root() / relative_path

def delete_document(relative_path: str) -> bool:
    """Deletes a document given its relative path."""
    try:
        path = get_absolute_path(relative_path)
        if path.exists() and path.is_file():
            path.unlink()
            return True
        return False
    except Exception:
        return False

def get_file_size_mb(path: str | Path) -> float:
    """Gets the file size in MB."""
    p = Path(path)
    if p.exists():
        return p.stat().st_size / (1024 * 1024)
    return 0.0

def is_allowed_image(path: str) -> bool:
    """Checks if the file extension corresponds to an allowed image format."""
    allowed = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    return Path(path).suffix.lower() in allowed

def is_allowed_document(path: str) -> bool:
    """Checks if the file extension corresponds to an allowed document format."""
    allowed = {'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.xls', '.xlsx'}
    return Path(path).suffix.lower() in allowed

def create_thumbnail(image_path: str, output_path: str | None = None, size: tuple = (150, 150)) -> str | None:
    """Creates a thumbnail for an image and saves it."""
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            img.thumbnail(size)
            if output_path is None:
                p = Path(image_path)
                output_path = str(p.with_name(f"{p.stem}_thumb{p.suffix}"))
            img.save(output_path)
            return output_path
    except Exception:
        return None

def list_documents(category: str) -> list[dict]:
    """Lists all documents within a specific category folder."""
    cat_dir = get_documents_dir() / category
    if not cat_dir.exists():
        return []
    docs = []
    for f in cat_dir.iterdir():
        if f.is_file():
            docs.append({
                'name': f.name,
                'path': str(f.relative_to(get_project_root())),
                'size_mb': get_file_size_mb(f)
            })
    return docs

def sanitize_filename(filename: str) -> str:
    """Sanitizes a filename by removing special characters."""
    filename = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
    return filename

def get_mime_type(path: str) -> str:
    """Gets the mime type for a file."""
    mime, _ = mimetypes.guess_type(path)
    return mime or 'application/octet-stream'
