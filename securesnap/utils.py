
import os, platform, subprocess
from pathlib import Path

SYSTEM_PATH_GUARDS = [
    r"C:\Windows",
    r"C:\Program Files",
    r"C:\Program Files (x86)",
    r"C:\ProgramData",
]

def is_windows() -> bool:
    return platform.system().lower() == "windows"

def _normalize(p: str) -> str:
    return str(Path(p).resolve())

def is_drive_root(p: str) -> bool:
    p = _normalize(p)
    return len(p) <= 3 and len(p) >= 2 and p[1] == ":"

def dangerous_path(p: str) -> bool:
    p = _normalize(p)
    if is_drive_root(p):
        return True
    if is_windows():
        for guard in SYSTEM_PATH_GUARDS:
            if p.lower().startswith(guard.lower()):
                return True
    return False

def get_drive_letter(p: str) -> str:
    p = _normalize(p)
    if is_windows() and len(p) > 1 and p[1] == ":":
        return p[:2]
    return ""

def run_cipher_wipe(drive_letter: str, log_cb=None):
    # Run Windows 'cipher /w:<drive>\' to wipe free space. Admin often required.
    if not is_windows():
        raise RuntimeError("cipher /w is Windows-only")
    if not drive_letter or ":" not in drive_letter:
        raise ValueError("Invalid drive letter")
    cmd = ["cmd.exe","/c",f"cipher /w:{drive_letter}\\"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        if log_cb: log_cb(line.rstrip())
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"cipher exited with code {proc.returncode}")
