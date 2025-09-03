# SecureSnap — Targeted File/Folder Wiper (Windows-first, Python/Tkinter)
SecureSnap is a **beginner-friendly but verifiable** data wiper. It overwrites selected files (and all files inside selected folders) before deleting them, then produces **signed evidence** you can verify later. An optional Windows **free-space scrub** can clean up previously deleted space on HDDs.

> **Important:** This tool can irreversibly erase data. Test on a dummy folder first. Do **not** point it at system directories or the root of a drive.

---

## ✨ What it does

- **Targeted wipe (main):** For a chosen file or folder, **overwrite → flush → delete**.  
  - Pattern: `zero` (default) or `random` (cryptographically strong).  
  - Passes: default `1` (generally sufficient for HDDs).  
  - Skips symlinks/junctions; blocks dangerous system paths and drive roots.
- **Signed certificate:** Writes a canonical `certificate.json` **signed with RSA-PSS (SHA-256)** + `certificate.json.sig`.  
  - Also writes `certificate.sha256`.  
  - Optional **PDF** containing run details, the JSON’s SHA-256, and a QR of that hash (for human cross-checks).
- **Optional free-space scrub (Windows / HDD):** Runs `cipher /w:<drive>` after the targeted wipe to overwrite unused space (useful on HDDs; **not recommended on SSDs**).
- **GUI and logs:** Tkinter app with progress bar, cancel button, dry-run preview, and a scrollable log.

---

## 🧰 Quick start (Windows)

1. **Install Python 3.10–3.12** and open a terminal inside the project folder (where `requirements.txt` lives).
2. (Recommended) Create and activate a virtualenv:
   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   # If PowerShell blocks scripts:
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\.venv\Scripts\Activate.ps1
