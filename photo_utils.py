"""
photo_utils.py  —  v0.5  (minimal, no image processing library required)

Rules
  • Accept JPG / JPEG / PNG / BMP up to 10 MB
  • Save raw bytes as-is under photos/<member_id>_<ts>.<ext>
  • Serve via /photos/<filename>  (handled in web_ui.py)
  • Display in tree via <img src="/photos/…"> + CSS object-fit
  • No PIL, no resizing, no base64 embedding
"""
import os
import time
from pathlib import Path

PHOTO_DIR = Path(os.environ.get("PHOTO_DIR", str(Path(__file__).parent / 'photos')))
PHOTO_DIR.mkdir(parents=True, exist_ok=True)

MAX_BYTES    = 10 * 1024 * 1024          # 10 MB
ALLOWED_EXTS = {'.jpg', '.jpeg', '.png', '.bmp'}
ALLOWED_MIME = {
    'image/jpeg', 'image/jpg', 'image/png',
    'image/bmp', 'image/x-ms-bmp', 'image/x-bmp',
}


class PhotoError(Exception):
    pass


# ─── public API ───────────────────────────────────────────────────────────────

def save_photo(member_id: int, file_bytes: bytes,
               original_name: str = '', mime: str = '') -> str:
    """Validate and save photo. Returns filename. Raises PhotoError on failure."""
    if not file_bytes:
        raise PhotoError("No file data")

    if len(file_bytes) > MAX_BYTES:
        mb = len(file_bytes) // 1024 // 1024
        raise PhotoError(f"File too large ({mb} MB). Max 10 MB.")

    ext = Path(original_name).suffix.lower() if original_name else ''
    if ext not in ALLOWED_EXTS:
        if mime.lower() in ALLOWED_MIME:
            ext = '.jpg'          # safe fallback
        else:
            raise PhotoError("Only JPG, PNG, BMP files are accepted.")

    filename = f"member_{member_id}_{int(time.time()*1000)}{ext}"
    (PHOTO_DIR / filename).write_bytes(file_bytes)
    return filename


def delete_photo(filename: str) -> None:
    """Delete a photo file safely."""
    if not filename:
        return
    path = PHOTO_DIR / Path(filename).name   # strip any path components
    if path.exists() and path.is_file():
        path.unlink()


def validate_path(filename: str) -> 'Path | None':
    """Return safe absolute Path or None if file not found / path invalid."""
    if not filename:
        return None
    safe = (PHOTO_DIR / Path(filename).name).resolve()
    try:
        safe.relative_to(PHOTO_DIR.resolve())   # must be inside PHOTO_DIR
        return safe if safe.is_file() else None
    except ValueError:
        return None


def photo_url(filename: str) -> str:
    """Return the URL path used to serve this photo."""
    return f'/photos/{Path(filename).name}' if filename else ''
