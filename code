import struct
import socket
import customtkinter as ctk

try:
    from pynput import keyboard as _kb
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

W, H           = 262, 300
BG             = "#0d0d0d"
FG_VAL         = "#7dffaa"
FG_LABEL       = "#4a6050"
FG_ERR         = "#ff6655"
FG_ACT         = "#ffaa44"
FG_SUBTLE      = "#1e2e1e"
BORDER_COLOR   = "#1e3025"

VERSION        = "v1.0"

def ip_to_int(ip: str) -> int:
    return struct.unpack("!I", socket.inet_aton(ip))[0]

def int_to_ip(n: int) -> str:
    return socket.inet_ntoa(struct.pack("!I", n & 0xFFFFFFFF))

def cidr_to_mask(c: int) -> int:
    return 0 if c == 0 else (0xFFFFFFFF << (32 - c)) & 0xFFFFFFFF

def validate_ip(raw: str) -> bool:
    try:
        socket.inet_aton(raw)
        return True
    except OSError:
        return False

class IPRechner:

    def __init__(self):
        self.alpha_ghost      = 0.12
        self.alpha_solid      = 0.75
        self.current_alpha    = 0.75
        self.hidden           = False
        self.minimized        = False
        self.topmost          = True
        self.hotkey_key       = "h"
        self.recording        = False
        self._drag            = {}
        self._pynput_listener = None

        self._build_window()
        self._build_ui()
        self._bind_local()
        self._start_global_hotkey()
        self._calculate()
        self.root.mainloop()

    def _build_window(self):
        self.root = ctk.CTk()
        self.root.title("IP-Rechner")
        self.root.geometry(f"{W}x{H}")
        self.root.resizable(False, False)
        self.root.overrideredirect(True)
        self.root.attributes("-alpha", self.current_alpha)
        self.root.attributes("-topmost", self.topmost)
        self.root.configure(fg_color=BG)

        self.root.update_idletasks()
        sx = self.root.winfo_screenwidth()
        sy = self.root.winfo_screenheight()
        self.root.geometry(f"{W}x{H}+{(sx - W) // 2}+{(sy - H) // 2}")

    def _build_ui(self):
        self._build_titlebar()
        self._build_content()

    def _build_titlebar(self):
        self._bar = ctk.CTkFrame(self.root, fg_color=FG_SUBTLE, height=24)
        self._bar.pack(fill="x")
        self._bar.pack_propagate(False)

        ctk.CTkLabel(
            self._bar, text="  IP-Rechner",
            font=("Consolas", 9), text_color="#3a5a3a", anchor="w"
        ).pack(side="left", fill="y")

        ctk.CTkButton(
            self._bar, text="×", width=24, height=20,
            fg_color="transparent", hover_color="#2a1a1a",
            text_color="#664444", font=("Consolas", 13),
            command=self._quit
        ).pack(side="right", padx=(0, 2))

        ctk.CTkButton(
            self._bar, text="–", width=24, height=20,
            fg_color="transparent", hover_color="#1a2a1a",
            text_color="#446644", font=("Consolas", 13),
            command=self._toggle_minimize
        ).pack(side="right")

        ctk.CTkButton(
            self._bar, text="⚙", width=24, height=20,
            fg_color="transparent", hover_color="#1a2a1a",
            text_color="#3a5a3a", font=("Consolas", 12),
            command=self._open_settings
        ).pack(side="right")

        for w in [self._bar] + list(self._bar.winfo_children()):
            w.bind("<ButtonPress-1>", self._drag_start)
            w.bind("<B1-Motion>",     self._drag_move)

    def _build_content(self):
        self._content = ctk.CTkFrame(self.root, fg_color="transparent")
        self._content.pack(fill="both", expand=True)

        self._build_inputs()
        self._sep()
        self._build_results()
        self._sep()
        self._build_bottom_bar()

    def _build_inputs(self):
        frame = ctk.CTkFrame(self._content, fg_color="transparent")
        frame.pack(fill="x", padx=8, pady=(6, 3))

        self.entry_ip = ctk.CTkEntry(
            frame, width=136, height=26, font=("Consolas", 11),
            fg_color="#141414", text_color="#c8ffd4",
            border_color=BORDER_COLOR, border_width=1,
            placeholder_text="192.168.1.0"
        )
        self.entry_ip.pack(side="left")
        self.entry_ip.insert(0, "192.168.1.0")

        ctk.CTkLabel(
            frame, text=" / ", font=("Consolas", 12),
            text_color="#405040"
        ).pack(side="left")

        self.entry_cidr = ctk.CTkEntry(
            frame, width=34, height=26, font=("Consolas", 11),
            fg_color="#141414", text_color="#c8ffd4",
            border_color=BORDER_COLOR, border_width=1,
            placeholder_text="24"
        )
        self.entry_cidr.pack(side="left")
        self.entry_cidr.insert(0, "24")

        ctk.CTkButton(
            frame, text="▶", width=26, height=26,
            font=("Consolas", 10),
            fg_color="#1a2e1a", hover_color="#2a4a2a",
            text_color=FG_VAL, command=self._calculate
        ).pack(side="left", padx=(5, 0))

    def _build_results(self):
        ROWS = [
            ("Netzadresse",  "net"),
            ("Broadcast",    "bc"),
            ("Subnetzmaske", "mask"),
            ("Erster Host",  "first"),
            ("Letzter Host", "last"),
            ("Hosts",        "hosts"),
        ]
        self.val_labels = {}
        for title, key in ROWS:
            row = ctk.CTkFrame(self._content, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=0)
            ctk.CTkLabel(
                row, text=title,
                font=("Consolas", 9), text_color=FG_LABEL,
                anchor="w", width=88
            ).pack(side="left")
            lbl = ctk.CTkLabel(
                row, text="", font=("Consolas", 10),
                text_color=FG_VAL, anchor="w"
            )
            lbl.pack(side="left")
            self.val_labels[key] = lbl

    def _build_bottom_bar(self):
        bar = ctk.CTkFrame(self._content, fg_color="transparent")
        bar.pack(fill="x", padx=8, pady=(3, 5))

        self.btn_hide = ctk.CTkButton(
            bar, text="hide", width=44, height=20,
            font=("Consolas", 9),
            fg_color="#1a1a2a", hover_color="#2a2a3a",
            text_color="#88aaff", command=self.toggle_visibility
        )
        self.btn_hide.pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            bar, text="ghost", width=46, height=20,
            font=("Consolas", 9),
            fg_color="#141414", hover_color="#222222",
            text_color="#446644",
            command=lambda: self._set_alpha(self.alpha_ghost)
        ).pack(side="left", padx=(0, 3))

        ctk.CTkButton(
            bar, text="solid", width=46, height=20,
            font=("Consolas", 9),
            fg_color="#141414", hover_color="#222222",
            text_color=FG_VAL,
            command=lambda: self._set_alpha(self.alpha_solid)
        ).pack(side="left")

    def _sep(self):
        ctk.CTkFrame(self._content, height=1, fg_color="#1e2e1e").pack(
            fill="x", padx=8, pady=2
        )

    def _calculate(self, *_):
        raw_ip  = self.entry_ip.get().strip()
        raw_cdr = self.entry_cidr.get().strip()

        def err(msg):
            for lbl in self.val_labels.values():
                lbl.configure(text="", text_color=FG_VAL)
            self.val_labels["net"].configure(text=msg, text_color=FG_ERR)

        if not validate_ip(raw_ip):
            err("Ungültige IP-Adresse")
            return
        try:
            c = int(raw_cdr)
            assert 0 <= c <= 32
        except (ValueError, AssertionError):
            err("CIDR muss 0–32 sein")
            return

        ip_int = ip_to_int(raw_ip)
        mask   = cidr_to_mask(c)
        net    = ip_int & mask
        bc     = net | (~mask & 0xFFFFFFFF)

        if c == 32:
            first, last, hosts = net, net, 1
        elif c == 31:
            first, last, hosts = net, bc, 2
        else:
            first = net + 1
            last  = bc  - 1
            hosts = bc  - net - 1

        self.val_labels["net"].configure(text=int_to_ip(net),    text_color=FG_VAL)
        self.val_labels["bc"].configure( text=int_to_ip(bc),     text_color=FG_VAL)
        self.val_labels["mask"].configure(
            text=f"{int_to_ip(mask)}  (/{c})", text_color=FG_VAL
        )
        self.val_labels["first"].configure(text=int_to_ip(first), text_color=FG_VAL)
        self.val_labels["last"].configure( text=int_to_ip(last),  text_color=FG_VAL)
        self.val_labels["hosts"].configure(
            text=f"{hosts:,}".replace(",", ".") + " Hosts",
            text_color=FG_VAL
        )

    def _set_alpha(self, val: float):
        self.current_alpha = max(0.05, min(1.0, val))
        if not self.hidden:
            self.root.attributes("-alpha", self.current_alpha)

    def toggle_visibility(self, *_):
        if self.recording:
            return
        self.hidden = not self.hidden
        if self.hidden:
            self.root.attributes("-alpha", 0.0)
            self.btn_hide.configure(text="show")
        else:
            self.root.attributes("-alpha", self.current_alpha)
            self.btn_hide.configure(text="hide")

    def _toggle_minimize(self):
        if self.minimized:
            self._content.pack(fill="both", expand=True)
            self.root.geometry(f"{W}x{H}")
            self.minimized = False
        else:
            self._content.pack_forget()
            self.root.geometry(f"{W}x24")
            self.minimized = True

    def _drag_start(self, e):
        if self.recording:
            return
        self._drag["x"] = e.x_root - self.root.winfo_x()
        self._drag["y"] = e.y_root - self.root.winfo_y()

    def _drag_move(self, e):
        if self.recording or not self._drag:
            return
        self.root.geometry(
            f"+{e.x_root - self._drag['x']}+{e.y_root - self._drag['y']}"
        )

    def _bind_local(self):
        self.entry_ip.bind("<Return>",   self._calculate)
        self.entry_cidr.bind("<Return>", self._calculate)
        self.root.bind("<Escape>",       lambda e: self._quit())
        self._bind_local_hotkey()

    def _bind_local_hotkey(self):
        k = self.hotkey_key.lower()
        for seq in (f"<{k}>", f"<{k.upper()}>"):
            try:
                self.root.bind(seq, self.toggle_visibility)
            except Exception:
                pass

    def _start_global_hotkey(self):
        if not PYNPUT_AVAILABLE:
            return
        self._stop_global_hotkey()

        def on_press(key):
            if self.recording:
                return
            try:
                char = key.char.lower() if hasattr(key, "char") and key.char else None
            except Exception:
                char = None
            if char == self.hotkey_key.lower():
                self.root.after(0, self.toggle_visibility)

        self._pynput_listener = _kb.Listener(on_press=on_press)
        self._pynput_listener.daemon = True
        self._pynput_listener.start()

    def _stop_global_hotkey(self):
        if self._pynput_listener is not None:
            try:
                self._pynput_listener.stop()
            except Exception:
                pass
            self._pynput_listener = None

    def _open_settings(self):
        if hasattr(self, "_settings_win") and self._settings_win.winfo_exists():
            self._settings_win.focus()
            return

        win = ctk.CTkToplevel(self.root)
        win.title("Einstellungen")
        win.geometry("280x310")
        win.resizable(False, False)
        win.attributes("-topmost", True)
        win.configure(fg_color="#0d0d0d")
        win.grab_set()
        self._settings_win = win

        ctk.CTkLabel(
            win, text=f"IP-Rechner {VERSION}",
            font=("Consolas", 12, "bold"), text_color=FG_VAL
        ).pack(pady=(10, 5))

        def section(text):
            ctk.CTkLabel(
                win, text=text, font=("Consolas", 9, "bold"),
                text_color=FG_LABEL
            ).pack(anchor="w", padx=12, pady=(10, 2))

        def card():
            f = ctk.CTkFrame(win, fg_color=FG_SUBTLE, corner_radius=5)
            f.pack(fill="x", padx=10, pady=(0, 2))
            return f

        def row(parent):
            r = ctk.CTkFrame(parent, fg_color="transparent")
            r.pack(fill="x", padx=8, pady=3)
            return r

        section("Hotkey")
        f_hk = card()
        r1 = row(f_hk)
        ctk.CTkLabel(r1, text="Taste:", font=("Consolas", 9),
                     text_color=FG_LABEL, width=68, anchor="w").pack(side="left")
        self._lbl_key = ctk.CTkLabel(
            r1, text=self.hotkey_key,
            font=("Consolas", 10), text_color=FG_VAL, width=54, anchor="w"
        )
        self._lbl_key.pack(side="left")
        ctk.CTkButton(
            r1, text="aufnehmen", width=74, height=20,
            font=("Consolas", 9),
            fg_color="#1e1a0e", hover_color="#2e2a1e",
            text_color=FG_LABEL, command=lambda: self._start_record(win)
        ).pack(side="right")

        if not PYNPUT_AVAILABLE:
            ctk.CTkLabel(
                win, text="  ⚠ pynput fehlt – nur bei Fokus aktiv",
                font=("Consolas", 8), text_color=FG_ACT
            ).pack(anchor="w", padx=12, pady=(0, 2))

        section("Transparenz")
        f_tr = card()

        r_g = row(f_tr)
        ctk.CTkLabel(r_g, text="ghost %:", font=("Consolas", 9),
                     text_color=FG_LABEL, width=68, anchor="w").pack(side="left")
        self._entry_ghost = ctk.CTkEntry(
            r_g, width=44, height=22, font=("Consolas", 10),
            fg_color="#141414", text_color="#c8ffd4",
            border_color=BORDER_COLOR, border_width=1
        )
        self._entry_ghost.insert(0, str(int(self.alpha_ghost * 100)))
        self._entry_ghost.pack(side="left")
        ctk.CTkLabel(r_g, text="%", font=("Consolas", 9),
                     text_color=FG_LABEL).pack(side="left", padx=(3, 0))

        r_s = row(f_tr)
        ctk.CTkLabel(r_s, text="solid %:", font=("Consolas", 9),
                     text_color=FG_LABEL, width=68, anchor="w").pack(side="left")
        self._entry_solid = ctk.CTkEntry(
            r_s, width=44, height=22, font=("Consolas", 10),
            fg_color="#141414", text_color="#c8ffd4",
            border_color=BORDER_COLOR, border_width=1
        )
        self._entry_solid.insert(0, str(int(self.alpha_solid * 100)))
        self._entry_solid.pack(side="left")
        ctk.CTkLabel(r_s, text="%", font=("Consolas", 9),
                     text_color=FG_LABEL).pack(side="left", padx=(3, 0))

        section("Fenster")
        f_win = card()
        r_top = row(f_win)
        ctk.CTkLabel(r_top, text="Immer vorne:", font=("Consolas", 9),
                     text_color=FG_LABEL, width=94, anchor="w").pack(side="left")
        self._topmost_var = ctk.BooleanVar(value=self.topmost)
        ctk.CTkSwitch(
            r_top, variable=self._topmost_var, text="",
            width=40, height=18,
            fg_color="#1a2e1a", progress_color="#3a6040",
            button_color="#50a060", button_hover_color="#60b070"
        ).pack(side="left")

        frame_btn = ctk.CTkFrame(win, fg_color="transparent")
        frame_btn.pack(fill="x", padx=10, pady=(8, 0))

        ctk.CTkButton(
            frame_btn, text="Übernehmen", width=108, height=24,
            font=("Consolas", 9),
            fg_color="#1a2e1a", hover_color="#2a4a2a",
            text_color=FG_VAL,
            command=lambda: self._apply_settings(win)
        ).pack(side="right", padx=(4, 0))

        ctk.CTkButton(
            frame_btn, text="Abbrechen", width=88, height=24,
            font=("Consolas", 9),
            fg_color="#1a1a1a", hover_color="#2a2a2a",
            text_color=FG_LABEL, command=win.destroy
        ).pack(side="right")

    def _apply_settings(self, win):
        try:
            g = int(self._entry_ghost.get())
            assert 1 <= g <= 99
            self.alpha_ghost = g / 100
        except (ValueError, AssertionError):
            pass
        try:
            s = int(self._entry_solid.get())
            assert 1 <= s <= 100
            self.alpha_solid = s / 100
        except (ValueError, AssertionError):
            pass

        self.topmost = self._topmost_var.get()
        self.root.attributes("-topmost", self.topmost)
        self._bind_local_hotkey()
        self._start_global_hotkey()
        win.destroy()

    def _start_record(self, parent_win):
        self.recording = True
        self._lbl_key.configure(text="[Taste drücken]", text_color=FG_ACT)
        parent_win.bind("<KeyPress>", lambda e: self._on_key_record(e, parent_win))
        parent_win.focus_set()

    def _on_key_record(self, e, parent_win):
        IGNORE = {
            "Shift_L", "Shift_R", "Control_L", "Control_R",
            "Alt_L",   "Alt_R",   "Super_L",   "Super_R",
            "Escape",  "Return",  "Tab"
        }
        if e.keysym in IGNORE:
            self._lbl_key.configure(text="[abgebrochen]", text_color=FG_ERR)
            self.root.after(1200, lambda: self._lbl_key.configure(
                text=self.hotkey_key, text_color=FG_VAL))
        else:
            self.hotkey_key = e.keysym.lower()
            self._lbl_key.configure(text=self.hotkey_key, text_color=FG_VAL)

        self.recording = False
        parent_win.unbind("<KeyPress>")

    def _quit(self):
        self._stop_global_hotkey()
        self.root.destroy()


if __name__ == "__main__":
    IPRechner()
