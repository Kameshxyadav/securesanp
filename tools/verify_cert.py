
import argparse, json, hashlib
from pathlib import Path
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    ap.add_argument("--sig", required=True)
    ap.add_argument("--pub", required=True)
    args = ap.parse_args()

    data_raw = Path(args.json).read_text(encoding="utf-8")
    data_sorted = json.dumps(json.loads(data_raw), separators=(",",":"), sort_keys=True).encode("utf-8")
    sig = Path(args.sig).read_bytes()
    pub = load_pem_public_key(Path(args.pub).read_bytes())

    try:
        pub.verify(sig, data_sorted, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256())
        print("VALID")
        print("SHA-256:", hashlib.sha256(data_sorted).hexdigest())
    except Exception as e:
        print("INVALID:", e)

if __name__ == "__main__":
    main()
