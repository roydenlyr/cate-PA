#!/usr/bin/env python3
# pylint: disable=E1101
"""
PA Audio System — Mesh Network Test Tool
Run from any machine on the network (Pi or laptop).
Requires: pip install requests
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import threading
import struct
import io
import wave
import math
import time
import json
import os
from datetime import datetime

PORT = 5000
TIMEOUT = 15
DEFAULT_STATIONS_PATH = os.path.expanduser("~/cate-PA/src/stations.json")

# Audio plays this many times on each station (change to 1 for single-play testing)
PLAY_COUNT = 2

SHORT_WAV_SEC = 1    # short tone for mesh, broadcast, stress tests
LONG_WAV_SEC = 3     # long tone for busy detection test

# ---------------------------------------------------------------------------
# Audio helpers
# ---------------------------------------------------------------------------

def generate_test_wav(duration_sec=1, freq=440, sample_rate=44100):
    """Generate a sine-wave WAV in memory and return raw bytes."""
    n_samples = int(sample_rate * duration_sec)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for i in range(n_samples):
            sample = int(32767 * 0.5 * math.sin(2 * math.pi * freq * i / sample_rate))
            wf.writeframes(struct.pack("<h", sample))
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def api_status(ip):
    r = requests.get(f"http://{ip}:{PORT}/status", timeout=TIMEOUT)
    return r.json()


def api_send(ip, target, wav_bytes):
    files = {"audio": ("test.wav", io.BytesIO(wav_bytes), "audio/wav")}
    data = {"target": target}
    r = requests.post(f"http://{ip}:{PORT}/send", files=files, data=data, timeout=TIMEOUT)
    return r.json()


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class PATestTool:
    def __init__(self, root):
        self.root = root
        self.root.title("PA System — Mesh Test Tool")
        self.root.geometry("1000x780")
        self.root.minsize(850, 650)

        self.stations = {}          # {id: ip}
        self.station_ids = []
        self.wav_short = generate_test_wav(duration_sec=SHORT_WAV_SEC, freq=440)
        self.wav_long = generate_test_wav(duration_sec=LONG_WAV_SEC, freq=440)
        self.running = False
        self.cells = {}

        self._build_ui()

    # ---- UI construction ----

    def _build_ui(self):
        # --- Stations file ---
        conn = ttk.LabelFrame(self.root, text="Stations", padding=10)
        conn.pack(fill="x", padx=10, pady=(10, 5))

        ttk.Label(conn, text="stations.json path:").pack(side="left")
        self.path_var = tk.StringVar(value=DEFAULT_STATIONS_PATH)
        ttk.Entry(conn, textvariable=self.path_var, width=45).pack(side="left", padx=5)
        ttk.Button(conn, text="Browse…", command=self._browse).pack(side="left", padx=2)
        ttk.Button(conn, text="Load", command=self._load_stations).pack(side="left", padx=2)
        self.conn_label = ttk.Label(conn, text="No stations loaded", foreground="grey")
        self.conn_label.pack(side="left", padx=10)

        # --- Test buttons ---
        btns = ttk.LabelFrame(self.root, text="Tests", padding=10)
        btns.pack(fill="x", padx=10, pady=5)

        self._buttons = {}
        for label, cmd in [
            ("Diagnostics",     self._cmd_diagnostics),
            ("Mesh Test",       self._cmd_mesh),
            ("Broadcast Test",  self._cmd_broadcast),
            ("Busy Detection",  self._cmd_busy),
            ("Stress Test",     self._cmd_stress),
            ("Run All",         self._cmd_all),
        ]:
            b = ttk.Button(btns, text=label, command=cmd, state="disabled")
            b.pack(side="left", padx=4)
            self._buttons[label] = b

        # --- Results matrix ---
        matrix_outer = ttk.LabelFrame(self.root, text="Results Matrix  (Sender → Target)", padding=10)
        matrix_outer.pack(fill="x", padx=10, pady=5)

        canvas = tk.Canvas(matrix_outer, height=160)
        h_scroll = ttk.Scrollbar(matrix_outer, orient="horizontal", command=canvas.xview)
        canvas.configure(xscrollcommand=h_scroll.set)
        h_scroll.pack(side="bottom", fill="x")
        canvas.pack(fill="x")

        self.matrix_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=self.matrix_frame, anchor="nw")
        self.matrix_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        self._matrix_canvas = canvas

        # --- Log ---
        log_frame = ttk.LabelFrame(self.root, text="Log", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        self.log_box = tk.Text(log_frame, height=14, font=("Courier", 9), wrap="word")
        sb = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log_box.pack(fill="both", expand=True)

        self.log_box.tag_config("ok",   foreground="#2e7d32")
        self.log_box.tag_config("fail", foreground="#c62828")
        self.log_box.tag_config("warn", foreground="#e65100")
        self.log_box.tag_config("info", foreground="#1565c0")
        self.log_box.tag_config("head", font=("Courier", 9, "bold"))

    # ---- Helpers ----

    def _log(self, msg, tag=""):
        """Thread-safe log append."""
        ts = datetime.now().strftime("%H:%M:%S")
        def _do():
            self.log_box.insert("end", f"[{ts}] {msg}\n", tag)
            self.log_box.see("end")
        self.root.after(0, _do)

    def _browse(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            self.path_var.set(path)

    def _load_stations(self):
        path = self.path_var.get().strip()
        try:
            with open(path) as f:
                self.stations = json.load(f)
            self.station_ids = sorted(self.stations.keys())
            self.conn_label.config(text=f"{len(self.stations)} stations loaded", foreground="green")
            self._log(f"Loaded stations: {', '.join(f'{s} ({self.stations[s]})' for s in self.station_ids)}", "info")
            for b in self._buttons.values():
                b.config(state="normal")
            self._build_matrix()
        except Exception as e:
            messagebox.showerror("Load error", str(e))

    def _set_buttons(self, enabled):
        state = "normal" if enabled else "disabled"
        for b in self._buttons.values():
            b.config(state=state)

    def _wait_until_idle(self, timeout=30):
        """Poll all stations until none are playing. Returns True if all idle."""
        start = time.time()
        while time.time() - start < timeout:
            all_idle = True
            for sid in self.station_ids:
                try:
                    data = api_status(self.stations[sid])
                    if data.get("playing", False):
                        all_idle = False
                        break
                except Exception:
                    pass
            if all_idle:
                return True
            time.sleep(0.5)
        return False

    def _threaded(self, fn):
        """Run fn in a background thread; disable buttons while running."""
        def wrapper():
            if self.running:
                return
            self.running = True
            self.root.after(0, lambda: self._set_buttons(False))
            try:
                fn()
            except Exception as e:
                self._log(f"Unexpected error: {e}", "fail")
            finally:
                self.running = False
                self.root.after(0, lambda: self._set_buttons(True))
        threading.Thread(target=wrapper, daemon=True).start()

    # ---- Matrix display ----

    def _build_matrix(self):
        for w in self.matrix_frame.winfo_children():
            w.destroy()
        self.cells.clear()

        targets = self.station_ids + ["BROADCAST"]

        ttk.Label(self.matrix_frame, text="From \\ To", font=("Courier", 8, "bold")).grid(
            row=0, column=0, padx=3, pady=3, sticky="w"
        )
        for j, t in enumerate(targets):
            ttk.Label(self.matrix_frame, text=t, font=("Courier", 8, "bold")).grid(
                row=0, column=j + 1, padx=3, pady=3
            )

        for i, sender in enumerate(self.station_ids):
            ttk.Label(self.matrix_frame, text=sender, font=("Courier", 8, "bold")).grid(
                row=i + 1, column=0, padx=3, pady=2, sticky="w"
            )
            for j, target in enumerate(targets):
                cell = tk.Label(
                    self.matrix_frame, text="—", width=8,
                    relief="sunken", bg="#e0e0e0", font=("Courier", 8),
                )
                cell.grid(row=i + 1, column=j + 1, padx=1, pady=1)
                self.cells[(sender, target)] = cell

    def _set_cell(self, sender, target, status):
        key = (sender, target)
        if key not in self.cells:
            return
        colours = {"ok": "#a5d6a7", "error": "#ef9a9a", "busy": "#ffe082", "timeout": "#ef9a9a"}
        bg = colours.get(status, "#e0e0e0")
        self.root.after(0, lambda: self.cells[key].config(text=status.upper(), bg=bg))

    # ==================================================================
    # TESTS
    # ==================================================================

    # ---- Diagnostics ----

    def _cmd_diagnostics(self):
        self._threaded(self._test_diagnostics)

    def _test_diagnostics(self):
        self._log("=" * 45, "head")
        self._log("DIAGNOSTICS — Reachability & Status", "head")
        self._log("=" * 45, "head")

        issues = []
        for sid in self.station_ids:
            ip = self.stations[sid]
            try:
                start = time.time()
                data = api_status(ip)
                latency = int((time.time() - start) * 1000)
                playing = data.get("playing", False)
                state = "PLAYING" if playing else "IDLE"
                tag = "warn" if playing else "ok"
                self._log(f"  {sid:>6}  {ip:>15}  {state:<8}  {latency} ms", tag)
                if playing:
                    issues.append(f"{sid} is currently playing")
            except requests.exceptions.ConnectTimeout:
                self._log(f"  {sid:>6}  {ip:>15}  TIMEOUT", "fail")
                issues.append(f"{sid} timed out")
            except Exception as e:
                self._log(f"  {sid:>6}  {ip:>15}  UNREACHABLE  {e}", "fail")
                issues.append(f"{sid} unreachable")

        if issues:
            self._log(f"Result: {len(issues)} issue(s) found", "fail")
            for issue in issues:
                self._log(f"  !! {issue}", "fail")
        else:
            self._log("Result: ALL STATIONS OK", "ok")

    # ---- Mesh test ----

    def _cmd_mesh(self):
        self._threaded(self._test_mesh)

    def _test_mesh(self):
        self._log("=" * 45, "head")
        self._log("MESH TEST — Every station → every station", "head")
        self._log("=" * 45, "head")
        self.root.after(0, self._build_matrix)
        time.sleep(0.2)

        unexpected = []

        for sender in self.station_ids:
            sender_ip = self.stations[sender]

            for target in self.station_ids:
                self._log(f"  {sender} → {target} ...", "info")
                try:
                    result = api_send(sender_ip, target, self.wav_short)
                    status = result.get("status", "error")
                    msg = result.get("message", "")
                    self._set_cell(sender, target, status)

                    tag = "ok" if status == "ok" else "fail"
                    self._log(f"    {status}: {msg}", tag)

                    if status != "ok":
                        unexpected.append(f"{sender} → {target}: {status} ({msg})")

                    # wait for playback to finish before next send
                    if not self._wait_until_idle():
                        self._log("    Stations still busy after timeout", "warn")

                except Exception as e:
                    self._set_cell(sender, target, "timeout")
                    self._log(f"    TIMEOUT: {e}", "fail")
                    unexpected.append(f"{sender} → {target}: timeout")

        self._report("Mesh test", unexpected)

    # ---- Broadcast test ----

    def _cmd_broadcast(self):
        self._threaded(self._test_broadcast)

    def _test_broadcast(self):
        self._log("=" * 45, "head")
        self._log("BROADCAST TEST — Every station → BROADCAST", "head")
        self._log("=" * 45, "head")

        unexpected = []

        for sender in self.station_ids:
            sender_ip = self.stations[sender]
            self._log(f"  {sender} → BROADCAST ...", "info")

            try:
                result = api_send(sender_ip, "BROADCAST", self.wav_short)
                details = result.get("details", {})

                all_ok = True
                for target, detail in details.items():
                    st = detail.get("status", "error")
                    msg = detail.get("message", "")
                    tag = "ok" if st == "ok" else "fail"
                    self._log(f"    → {target}: {st} — {msg}", tag)
                    if st != "ok":
                        all_ok = False
                        unexpected.append(f"{sender} → BROADCAST → {target}: {st}")

                self._set_cell(sender, "BROADCAST", "ok" if all_ok else "error")
                if not self._wait_until_idle():
                    self._log("    Stations still busy after timeout", "warn")

            except Exception as e:
                self._set_cell(sender, "BROADCAST", "timeout")
                self._log(f"    TIMEOUT: {e}", "fail")
                unexpected.append(f"{sender} → BROADCAST: timeout")

        self._report("Broadcast test", unexpected)

    # ---- Busy detection ----

    def _cmd_busy(self):
        self._threaded(self._test_busy)

    def _test_busy(self):
        self._log("=" * 45, "head")
        self._log("BUSY DETECTION TEST", "head")
        self._log("=" * 45, "head")
        self._log(f"  Sending {LONG_WAV_SEC} s audio (x{PLAY_COUNT}) via BROADCAST, then trying individual sends.", "info")

        unexpected = []

        # Use first station to broadcast long audio to occupy all stations
        broadcaster = self.station_ids[0]
        broadcaster_ip = self.stations[broadcaster]

        self._log(f"  Broadcasting long audio from {broadcaster} ...", "info")
        try:
            bcast_result = api_send(broadcaster_ip, "BROADCAST", self.wav_long)
            self._log(f"    Broadcast accepted: {bcast_result.get('status')}", "ok")
        except Exception as e:
            self._log(f"    Broadcast failed: {e}  — aborting busy test", "fail")
            return

        # Give audio a moment to start playing
        time.sleep(1)

        # Now try sending to each station — expect busy
        for sid in self.station_ids:
            ip = self.stations[sid]
            self._log(f"  Sending to {sid} while busy ...", "info")
            try:
                result = api_send(ip, sid, self.wav_short)
                status = result.get("status", "error")
                msg = result.get("message", "")

                if status == "busy":
                    self._log(f"    {status}: {msg}  (expected)", "ok")
                else:
                    self._log(f"    {status}: {msg}  (expected BUSY!)", "fail")
                    unexpected.append(f"{sid}: expected busy, got {status}")
            except Exception as e:
                self._log(f"    TIMEOUT: {e}", "fail")
                unexpected.append(f"{sid}: timeout during busy check")

        # Wait for long audio to finish, then verify idle
        self._log("  Waiting for playback to finish ...", "info")
        idle_timeout = LONG_WAV_SEC * PLAY_COUNT + 5
        if self._wait_until_idle(timeout=idle_timeout):
            self._log("  All stations idle", "ok")
        else:
            self._log("  Checking which stations are still busy ...", "warn")
            for sid in self.station_ids:
                ip = self.stations[sid]
                try:
                    data = api_status(ip)
                    if data.get("playing", False):
                        self._log(f"    {sid}: still playing (unexpected)", "fail")
                        unexpected.append(f"{sid}: still playing after timeout")
                    else:
                        self._log(f"    {sid}: idle", "ok")
                except Exception as e:
                    self._log(f"    {sid}: unreachable — {e}", "fail")

        self._report("Busy detection test", unexpected)

    # ---- Stress test ----

    def _cmd_stress(self):
        self._threaded(self._test_stress)

    def _test_stress(self):
        self._log("=" * 45, "head")
        self._log("STRESS TEST — Simultaneous broadcasts from all stations", "head")
        self._log("=" * 45, "head")

        results = {}
        threads = []

        def bcast_from(sid):
            ip = self.stations[sid]
            try:
                results[sid] = api_send(ip, "BROADCAST", self.wav_short)
            except Exception as e:
                results[sid] = {"status": "error", "message": str(e)}

        self._log("  Launching simultaneous broadcasts ...", "info")
        for sid in self.station_ids:
            t = threading.Thread(target=bcast_from, args=(sid,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=TIMEOUT + 5)

        errors = []
        for sid in self.station_ids:
            r = results.get(sid, {"status": "error", "message": "no response"})
            status = r.get("status", "error")
            msg = r.get("message", "")

            details = r.get("details", {})
            detail_summary = []
            for target, d in details.items():
                st = d.get("status", "error")
                detail_summary.append(f"{target}={st}")
                if st == "error":
                    errors.append(f"{sid} → {target}: error")

            tag = "ok" if status in ("ok",) else "warn" if status == "busy" else "fail"
            self._log(f"  {sid}: {status} — {msg}", tag)
            if detail_summary:
                self._log(f"    Details: {', '.join(detail_summary)}", "info")

        # In a stress test, busy is expected; only errors are flagged
        if errors:
            self._log(f"Result: {len(errors)} error(s) — busy responses are expected under contention", "fail")
            for e in errors:
                self._log(f"  !! {e}", "fail")
        else:
            self._log("Result: COMPLETE — no errors (busy responses are normal under contention)", "ok")

        self._wait_until_idle()

    # ---- Run all ----

    def _cmd_all(self):
        self._threaded(self._test_all)

    def _test_all(self):
        self._test_diagnostics()
        self._wait_until_idle()
        self._test_mesh()
        self._wait_until_idle()
        self._test_broadcast()
        self._wait_until_idle()
        self._test_busy()
        self._wait_until_idle()
        self._test_stress()
        self._log("=" * 45, "head")
        self._log("ALL TESTS COMPLETE", "head")
        self._log("=" * 45, "head")

    # ---- Reporting ----

    def _report(self, name, unexpected):
        if unexpected:
            self._log(f"Result: {name} — {len(unexpected)} UNEXPECTED result(s)", "fail")
            for u in unexpected:
                self._log(f"  !! {u}", "fail")
        else:
            self._log(f"Result: {name} — ALL PASSED", "ok")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = PATestTool(root)
    root.mainloop()