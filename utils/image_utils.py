from PIL import Image, ImageOps
import base64
from pathlib import Path
from io import BytesIO

def resize_image(path: str, max_width: int, max_height: int, output_path: str | None = None) -> str:
    """Resizes an image to fit within the specified maximum dimensions."""
    with Image.open(path) as img:
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        if output_path is None:
            p = Path(path)
            output_path = str(p.with_name(f"{p.stem}_resized{p.suffix}"))
        img.save(output_path)
        return output_path

def convert_to_jpeg(path: str, quality: int = 90) -> str:
    """Converts an image to JPEG format."""
    with Image.open(path) as img:
        rgb_im = img.convert('RGB')
        p = Path(path)
        output_path = str(p.with_name(f"{p.stem}.jpg"))
        rgb_im.save(output_path, 'JPEG', quality=quality)
        return output_path

def compress_image(path: str, quality: int = 85, output_path: str | None = None) -> str:
    """Compresses an image using Pillow to reduce file size."""
    with Image.open(path) as img:
        if output_path is None:
            p = Path(path)
            output_path = str(p.with_name(f"{p.stem}_compressed{p.suffix}"))
        if img.format == 'JPEG':
            img.save(output_path, 'JPEG', quality=quality)
        elif img.format == 'PNG':
            img.save(output_path, 'PNG', optimize=True)
        else:
            img.save(output_path)
        return output_path

def get_image_dimensions(path: str) -> tuple[int, int]:
    """Returns the width and height of an image."""
    with Image.open(path) as img:
        return img.size

def create_square_thumbnail(path: str, size: int = 150, output_path: str | None = None) -> str:
    """Creates a center-cropped square thumbnail."""
    with Image.open(path) as img:
        thumb = ImageOps.fit(img, (size, size), Image.Resampling.LANCZOS)
        if output_path is None:
            p = Path(path)
            output_path = str(p.with_name(f"{p.stem}_sq_thumb{p.suffix}"))
        thumb.save(output_path)
        return output_path

def image_to_base64(path: str) -> str:
    """Converts an image to a base64 encoded data URI."""
    with Image.open(path) as img:
        buffered = BytesIO()
        fmt = img.format if img.format else "PNG"
        img.save(buffered, format=fmt)
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/{fmt.lower()};base64,{img_str}"

def is_valid_image(path: str) -> bool:
    """Checks if a file is a valid image format supported by Pillow."""
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False
