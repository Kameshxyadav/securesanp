
from __future__ import annotations
import json, os, hashlib, platform
from pathlib import Path
from typing import Dict, Any, Tuple

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.graphics import renderPDF
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.barcode import qr as qrmod
    HAVE_PDF = True
except Exception:
    HAVE_PDF = False

KEYS_DIR = Path("Keys")
CERTS_DIR = Path("Certificates")

def ensure_keys() -> Tuple[Path, Path]:
    KEYS_DIR.mkdir(parents=True, exist_ok=True)
    prv = KEYS_DIR / "private.pem"
    pub = KEYS_DIR / "public.pem"
    if not prv.exists() or not pub.exists():
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        prv.write_bytes(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
        pub.write_bytes(key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
    return prv, pub

def build_payload(*, run_id: str, version: str, targets: list, summary: dict, started_utc: str, ended_utc: str, status: str) -> Dict[str, Any]:
    return {
        "id": run_id,
        "tool": {"name":"SecureSnap Wiper","version":version},
        "host": {"computer": platform.node(), "os": platform.platform()},
        "targets": targets,
        "summary": summary,
        "start_time_utc": started_utc,
        "end_time_utc": ended_utc,
        "status": status
    }

def sign_payload(payload: Dict[str, Any], prv_path: Path) -> bytes:
    data = json.dumps(payload, separators=(",",":"), sort_keys=True).encode("utf-8")
    key = serialization.load_pem_private_key(prv_path.read_bytes(), password=None)
    sig = key.sign(data, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256())
    return sig

def write_certificate(payload: Dict[str, Any]) -> Path:
    run_id = payload["id"]
    out_dir = CERTS_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # JSON (pretty + canonical for sig)
    pretty = json.dumps(payload, indent=2)
    canon = json.dumps(payload, separators=(",",":"), sort_keys=True).encode("utf-8")
    (out_dir / "certificate.json").write_text(pretty, encoding="utf-8")

    prv, pub = ensure_keys()
    sig = sign_payload(payload, prv)
    (out_dir / "certificate.json.sig").write_bytes(sig)
    (out_dir / "public.pem").write_bytes(pub.read_bytes())

    sha = hashlib.sha256(canon).hexdigest()
    (out_dir / "certificate.sha256").write_text(sha, encoding="utf-8")

    if HAVE_PDF:
        pdf = out_dir / "certificate.pdf"
        c = canvas.Canvas(str(pdf), pagesize=A4)
        W,H = A4
        y = H - 50
        c.setFont("Helvetica-Bold", 16); c.drawString(50, y, "WIPE OPERATION CERTIFICATE"); y -= 24
        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"Run ID: {run_id}"); y -= 14
        c.drawString(50, y, f"Status: {payload['status']}"); y -= 14
        c.drawString(50, y, f"Start (UTC): {payload['start_time_utc']}"); y -= 14
        c.drawString(50, y, f"End   (UTC): {payload['end_time_utc']}"); y -= 20
        c.setFont("Helvetica-Bold", 12); c.drawString(50, y, "Summary"); y -= 16
        c.setFont("Helvetica", 10)
        c.drawString(60, y, f"Files wiped: {payload['summary'].get('files',0)}"); y -= 14
        c.drawString(60, y, f"Folders processed: {payload['summary'].get('folders',0)}"); y -= 14
        c.drawString(60, y, f"Total bytes overwritten: {payload['summary'].get('total_bytes_overwritten',0)}"); y -= 22
        c.setFont("Helvetica-Bold", 12); c.drawString(50, y, "SHA-256 of certificate.json"); y -= 16
        c.setFont("Helvetica", 9); c.drawString(60, y, sha)
        try:
            qr = qrmod.QrCodeWidget(sha)
            bounds = qr.getBounds()
            size = 100
            w = bounds[2]-bounds[0]; h = bounds[3]-bounds[1]
            d = Drawing(size, size)
            d.add(qr)
            renderPDF.draw(d, c, W-140, 80)
        except Exception:
            pass
        c.showPage(); c.save()

    return out_dir / "certificate.json"
