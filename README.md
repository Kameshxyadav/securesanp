# SecureSnap — Targeted File/Folder Wiper (Windows-first, Python/Tkinter)
**SecureSnap** wipes selected files (and all files inside selected folders) and creates **verifiable proof** of the action.

> ⚠️ This permanently deletes data. Test on a dummy folder first.

---

## What it does

- **Targeted wipe (main):** Overwrite → flush → delete for each file.
  - Pattern: `zero` (default) or `random`
  - Passes: default `1`
  - Skips symlinks/junctions and blocks system paths/drive roots
- **Proof of wipe:**  
  - `Certificates/<RUN_ID>/certificate.json` (source of truth)  
  - `certificate.json.sig` (RSA-PSS, SHA-256) + `certificate.sha256`  
  - Optional `certificate.pdf` (if `reportlab` installed) with the JSON hash + QR
- **Optional free-space scrub (Windows/HDD):** Runs `cipher /w:<drive>` after the targeted wipe to clean previously deleted space (not recommended for SSDs).
- **GUI:** Progress bar, Cancel button, Dry-run preview, log window.

---

## Quick start (Windows)

1) **Install Python 3.10–3.12**  
2) Open a terminal **inside the project folder** (where `requirements.txt` is).  
3) (Recommended) Create and activate a virtual env:
```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
# If PowerShell blocks scripts:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

