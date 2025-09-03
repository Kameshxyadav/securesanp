
from __future__ import annotations
import threading, uuid, datetime, tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from securesnap.wipe import wipe_paths, plan
from securesnap.certs import build_payload, write_certificate
from securesnap.utils import dangerous_path, get_drive_letter, run_cipher_wipe, is_windows

VERSION = "1.0.1"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SecureSnap")
        self.geometry("760x560")
        self.resizable(False, False)

        self.targets = []
        self._cancel = False

        top = ttk.Frame(self); top.pack(fill="x", padx=10, pady=8)
        self.path_var = tk.StringVar()
        e = ttk.Entry(top, textvariable=self.path_var); e.pack(side="left", fill="x", expand=True, padx=(0,8))
        ttk.Button(top, text="Browse File", command=self.pick_file).pack(side="left")
        ttk.Button(top, text="Browse Folder", command=self.pick_folder).pack(side="left", padx=6)

        opts = ttk.LabelFrame(self, text="Options"); opts.pack(fill="x", padx=10, pady=6)
        self.passes_var = tk.IntVar(value=1)
        self.method_var = tk.StringVar(value="zero")
        self.dry_var = tk.BooleanVar(value=False)
        self.freespace_var = tk.BooleanVar(value=False)
        ttk.Label(opts, text="Passes:").grid(row=0, column=0, padx=8, pady=6, sticky="w")
        ttk.Spinbox(opts, from_=1, to=5, textvariable=self.passes_var, width=5).grid(row=0, column=1, sticky="w")
        ttk.Label(opts, text="Pattern:").grid(row=0, column=2, padx=8, sticky="w")
        ttk.Combobox(opts, values=["zero","random"], textvariable=self.method_var, width=10, state="readonly").grid(row=0, column=3, sticky="w")
        ttk.Checkbutton(opts, text="Dry-run (no erase)", variable=self.dry_var).grid(row=0, column=4, padx=8, sticky="w")
        ttk.Checkbutton(opts, text="Free-space scrub after wipe (HDD, Windows)", variable=self.freespace_var).grid(row=1, column=0, columnspan=5, padx=8, sticky="w")

        act = ttk.Frame(self); act.pack(fill="x", padx=10, pady=6)
        self.start_btn = ttk.Button(act, text="Wipe", command=self.start_wipe); self.start_btn.pack(side="left")
        self.cancel_btn = ttk.Button(act, text="Cancel", command=self.cancel, state="disabled"); self.cancel_btn.pack(side="left", padx=8)

        prog = ttk.LabelFrame(self, text="Progress"); prog.pack(fill="x", padx=10, pady=6)
        self.pbar = ttk.Progressbar(prog, orient="horizontal", mode="determinate", length=720)
        self.pbar.pack(padx=8, pady=6)
        self.status = tk.StringVar(value="Idle"); ttk.Label(prog, textvariable=self.status).pack(padx=8, anchor="w")

        logf = ttk.LabelFrame(self, text="Log"); logf.pack(fill="both", expand=True, padx=10, pady=(0,10))
        self.log = tk.Text(logf, height=14, wrap="word"); self.log.pack(fill="both", expand=True, padx=6, pady=6)

    def pick_file(self):
        p = filedialog.askopenfilename()
        if p:
            self.targets = [p]
            self.path_var.set(p)

    def pick_folder(self):
        p = filedialog.askdirectory()
        if p:
            self.targets = [p]
            self.path_var.set(p)

    def log_write(self, s: str):
        self.log.insert("end", s + "\n"); self.log.see("end")

    def set_status(self, s: str):
        self.status.set(s); self.update_idletasks()

    def cancel(self):
        self._cancel = True; self.set_status("Cancel requested…")

    def start_wipe(self):
        p = self.path_var.get().strip()
        if not p:
            messagebox.showwarning("Select target", "Choose a file or folder")
            return
        if dangerous_path(p):
            messagebox.showerror("Blocked path", "That location looks unsafe (system folder or drive root). Choose another.")
            return

        files, total, file_count, folder_count = plan([p])
        if self.dry_var.get():
            self.log_write(f"[DRY-RUN] Would wipe {file_count} files across {folder_count or 0} folder(s), total ~{total} bytes")
            for f in files[:80]:
                self.log_write("  - " + str(f))
            if len(files) > 80:
                self.log_write(f"  … and {len(files)-80} more")
            return

        if not files:
            messagebox.showwarning("Nothing to wipe", "No files found under the selected target.")
            return

        self._cancel = False
        self.start_btn.config(state="disabled"); self.cancel_btn.config(state="normal")
        self.pbar["value"] = 0; self.pbar["maximum"] = total
        self.log.delete("1.0","end")
        self.log_write(f"Starting wipe: {file_count} files (~{total} bytes)")

        t = threading.Thread(target=self._run_wipe, args=(p, total, file_count, folder_count))
        t.daemon = True; t.start()

    def _run_wipe(self, p, total, file_count, folder_count):
        started = datetime.datetime.utcnow().isoformat()
        def progress(done, tot, msg):
            self.pbar["value"] = done
            self.set_status(msg)

        try:
            bytes_done, failed = wipe_paths([p], passes=self.passes_var.get(), method=self.method_var.get(), progress=progress, cancel=lambda: self._cancel)
            status = "cancelled" if self._cancel else ("partial-failure" if failed else "success")
            ended = datetime.datetime.utcnow().isoformat()
            run_id = str(uuid.uuid4())
            payload = build_payload(
                run_id=run_id,
                version=VERSION,
                targets=[{"path": p, "type": "folder" if Path(p).is_dir() else "file"}],
                summary={"files": file_count, "folders": folder_count, "total_bytes_overwritten": int(bytes_done), "failed": failed},
                started_utc=started,
                ended_utc=ended,
                status=status
            )
            cert = write_certificate(payload)
            self.log_write(f"Certificate: {cert}")
            if failed:
                self.log_write("Failed items:")
                for f in failed[:50]:
                    self.log_write("  - " + f)
            if (not self._cancel) and self.freespace_var.get() and is_windows():
                drv = get_drive_letter(p)
                self.log_write(f"[cipher] Starting free-space scrub on {drv} (long running)")
                try:
                    run_cipher_wipe(drv, log_cb=lambda s: self.log_write("[cipher] " + s))
                except Exception as e:
                    self.log_write(f"[cipher] Skipped/failed: {e}")
        except Exception as e:
            self.log_write(f"ERROR: {e}")
        finally:
            self.start_btn.config(state="normal"); self.cancel_btn.config(state="disabled")
            self.set_status("Idle")

def main():
    app = App()
    app.mainloop()
