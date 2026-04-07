import os
import shutil
import glob
import time
import datetime


# ═══════════════════════════════════════════════
# BASIC OPERATIONS
# ═══════════════════════════════════════════════
def list_files(path: str = ".") -> list:
    try:
        entries = os.listdir(path)
        # Sort: folders first, then files
        dirs  = sorted([e for e in entries if os.path.isdir(os.path.join(path, e))])
        files = sorted([e for e in entries if os.path.isfile(os.path.join(path, e))])
        return dirs + files
    except Exception as e:
        return [str(e)]


def read_file(path: str, max_chars: int = 5000) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(max_chars)
        if os.path.getsize(path) > max_chars:
            content += f"\n… (file truncated, total {os.path.getsize(path)} bytes)"
        return content
    except Exception as e:
        return f"[read_file error] {e}"


def write_file(path: str, content: str) -> str:
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File written: {path} ({len(content)} chars)"
    except Exception as e:
        return f"[write_file error] {e}"


def append_file(path: str, content: str) -> str:
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
        return f"Appended to {path}"
    except Exception as e:
        return f"[append_file error] {e}"


def delete_file(path: str) -> str:
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
            return f"Folder deleted: {path}"
        os.remove(path)
        return f"File deleted: {path}"
    except Exception as e:
        return f"[delete_file error] {e}"


def create_folder(path: str) -> str:
    try:
        os.makedirs(path, exist_ok=True)
        return f"Folder created: {path}"
    except Exception as e:
        return f"[create_folder error] {e}"


def move_file(src: str, dst: str) -> str:
    try:
        shutil.move(src, dst)
        return f"Moved: {src} → {dst}"
    except Exception as e:
        return f"[move_file error] {e}"


def copy_file(src: str, dst: str) -> str:
    try:
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        return f"Copied: {src} → {dst}"
    except Exception as e:
        return f"[copy_file error] {e}"


def rename_file(src: str, new_name: str) -> str:
    try:
        parent = os.path.dirname(src)
        dst = os.path.join(parent, new_name)
        os.rename(src, dst)
        return f"Renamed: {src} → {dst}"
    except Exception as e:
        return f"[rename error] {e}"


# ═══════════════════════════════════════════════
# SEARCH & INFO
# ═══════════════════════════════════════════════
def search_files(pattern: str, root: str = ".") -> list:
    """Recursively search for files matching a glob pattern."""
    try:
        matches = glob.glob(os.path.join(root, "**", pattern), recursive=True)
        return matches[:50]  # cap results
    except Exception as e:
        return [str(e)]


def file_info(path: str) -> str:
    try:
        stat = os.stat(path)
        size = stat.st_size
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d %b %Y %H:%M")
        kind = "Folder" if os.path.isdir(path) else "File"
        size_str = (
            f"{size // 1024 // 1024} MB" if size > 1_000_000
            else f"{size // 1024} KB" if size > 1000
            else f"{size} bytes"
        )
        return f"{kind}: {os.path.basename(path)} | Size: {size_str} | Modified: {mtime}"
    except Exception as e:
        return f"[file_info error] {e}"


def recent_files(folder: str = ".", n: int = 10) -> list:
    """Return the n most recently modified files in folder."""
    try:
        files = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, f))
        ]
        files.sort(key=os.path.getmtime, reverse=True)
        return files[:n]
    except Exception as e:
        return [str(e)]


# ═══════════════════════════════════════════════
# ZIP / OPEN
# ═══════════════════════════════════════════════
def zip_folder(folder: str, output: str = None) -> str:
    try:
        if output is None:
            output = folder.rstrip("/\\") + ".zip"
        shutil.make_archive(output.replace(".zip", ""), "zip", folder)
        return f"Zipped: {output}"
    except Exception as e:
        return f"[zip error] {e}"


def unzip_file(zip_path: str, extract_to: str = ".") -> str:
    try:
        shutil.unpack_archive(zip_path, extract_to)
        return f"Extracted: {zip_path} → {extract_to}"
    except Exception as e:
        return f"[unzip error] {e}"


def open_file(path: str) -> str:
    """Open a file with its default application."""
    try:
        os.startfile(path)
        return f"Opened: {path}"
    except Exception as e:
        return f"[open error] {e}"
