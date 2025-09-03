
from __future__ import annotations
import os, secrets
from pathlib import Path
from typing import Callable, List, Tuple, Iterable

CHUNK = 16 * 1024 * 1024  # 16 MB

ProgressCb = Callable[[int, int, str], None]  # (bytes_done_total, bytes_total, status_text)
CancelCb = Callable[[], bool]

def _iter_files(root: Path) -> Iterable[Path]:
    for dp, dn, fn in os.walk(root, topdown=True, followlinks=False):
        dirpath = Path(dp)
        if dirpath.is_symlink():
            continue
        for name in fn:
            p = dirpath / name
            if p.is_symlink():
                continue
            yield p

def _file_len(p: Path) -> int:
    try:
        return p.stat().st_size
    except FileNotFoundError:
        return 0

def plan(paths: List[str]) -> Tuple[List[Path], int, int, int]:
    files: List[Path] = []
    total = 0
    file_count = 0
    folder_count = 0
    for raw in paths:
        p = Path(raw)
        if p.is_file():
            files.append(p); file_count += 1; total += _file_len(p)
        elif p.is_dir():
            folder_count += 1
            for f in _iter_files(p):
                if f.is_file():
                    files.append(f); file_count += 1; total += _file_len(f)
    return files, total, file_count, folder_count

def wipe_file(p: Path, passes: int, method: str,
              progress_file: Callable[[int, int, str], None],
              cancel: CancelCb) -> int:
    if not p.exists() or not p.is_file():
        return 0
    try: os.chmod(p, 0o666)
    except Exception: pass

    length = _file_len(p)
    done = 0
    with open(p, "r+b", buffering=0) as f:
        for _ in range(passes):
            f.seek(0)
            remaining = length
            while remaining > 0:
                if cancel and cancel():
                    progress_file(done, length, f"Cancel requested: {p.name}")
                    return done
                n = min(remaining, CHUNK)
                buf = (b"\x00" * n) if method == "zero" else secrets.token_bytes(n)
                f.write(buf)
                remaining -= n
                done += n
                progress_file(done, length, f"Wiping {p.name}")
            f.flush()
            os.fsync(f.fileno())
    try:
        with open(p, "r+b", buffering=0) as f:
            f.truncate(0); f.flush(); os.fsync(f.fileno())
    except Exception:
        pass
    try:
        p.unlink()
    except Exception:
        try: os.remove(str(p))
        except Exception: pass
    return length

def wipe_paths(targets: List[str], passes: int = 1, method: str = "zero",
               progress: ProgressCb = lambda a,b,c: None,
               cancel: CancelCb = lambda : False) -> Tuple[int, List[str]]:
    files, total, _, _ = plan(targets)
    bytes_total = total
    bytes_done_total = 0
    failed: List[str] = []
    for p in files:
        try:
            def progress_file(done, length, msg):
                progress(bytes_done_total + done, bytes_total, msg)
            written = wipe_file(p, passes, method, progress_file, cancel)
            bytes_done_total += written
        except Exception as e:
            failed.append(str(p))
            progress(bytes_done_total, bytes_total, f"Error on {p}: {e}")
        if cancel and cancel():
            break
    for t in targets:
        path = Path(t)
        if path.is_dir():
            for dp, dn, fn in os.walk(path, topdown=False, followlinks=False):
                try: os.rmdir(dp)
                except OSError: pass
            try: os.rmdir(path)
            except OSError: pass
    progress(bytes_done_total, bytes_total, "Done")
    return bytes_done_total, failed
