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
```
4) Install packages:
 ```powershell
   python -m pip install --upgrade pip
pip install -r requirements.txt
```
5)Run the app: 
```powershell
python run_gui.py
```
## How to use

Click Browse File or Browse Folder

(Optional) tick Dry-run to preview what would be wiped

Choose Passes and Pattern

Click Wipe

Outputs are saved in Certificates/<RUN_ID>/. Keys are created in Keys/ on first run.
## Verify the certificate
```powershell
python tools\verify_cert.py `
  --json Certificates\<RUN_ID>\certificate.json `
  --sig  Certificates\<RUN_ID>\certificate.json.sig `
  --pub  Keys\public.pem
```
You should see VALID and the SHA-256 of the JSON.
The PDF (if created) is just a readable summary.

## Notes & limits

HDD vs SSD: Overwrites are reliable on HDDs. On SSDs, wear-leveling/TRIM means overwrites may not purge old cells. For strict purge, use device Secure Erase/Crypto Erase (not included).

In-use files: If a file is open/locked (e.g., OneDrive/Office), close the app or pause sync and try again.

Paths: Don’t point at system folders or drive roots. Use Dry-run first.

## Project layout
```bash
SecureSnap/
├─ app/gui.py           # Tkinter GUI
├─ securesnap/wipe.py   # File/folder wiping
├─ securesnap/certs.py  # Keys, signed JSON, optional PDF
├─ securesnap/utils.py  # Guardrails, cipher /w helper
├─ tools/verify_cert.py # Verifier (JSON + sig)
├─ run_gui.py
├─ requirements.txt
└─ LICENSE
```
## License 
MIT


