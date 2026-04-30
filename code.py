import struct
import socket
import customtkinter as ctk
import json
import os
import threading
import ctypes
import ctypes.wintypes
import time
import sys

try:
    import pystray
    from PIL import Image, ImageDraw, ImageFont
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False

try:
    from pynput import keyboard as _kb
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

W, H           = 220, 260
BG             = "#0a0a0a"
FG_VAL         = "#8fce9f"
FG_LABEL       = "#5a8a6a"
FG_ERR         = "#aa4433"
FG_ACT         = "#886622"
FG_SUBTLE      = "#101010"
BORDER_COLOR   = "#151515"

VERSION        = "v2.0"
CONFIG_FILE    = os.path.expanduser("~/.ip_rechner_config.json")

WM_HOTKEY       = 0x0312
MOD_CONTROL     = 0x0002
MOD_ALT         = 0x0001
_HOTKEY_ID      = 1

LANG = "de"
STRINGS = {
    "de": {
        "title":       "IP-Rechner",
        "network":     "Netzadresse",
        "broadcast":   "Broadcast",
        "mask":        "Subnetzmaske",
        "first":       "Erster Host",
        "last":        "Letzter Host",
        "hosts":       "Hosts",
        "invalid_ip":  "Ungültige IP-Adresse",
        "invalid_cidr":"CIDR muss 0–32 sein",
        "settings":    "Einstellungen",
        "hotkey":      "Hotkey",
        "key":         "Taste:",
        "record":      "aufnehmen",
        "transparency":"Transparenz",
        "ghost":       "ghost %:",
        "solid":       "solid %:",
        "window":      "Fenster",
        "topmost":     "Immer vorne:",
        "apply":       "Speichern",
        "cancel":      "Abbrechen",
        "language":    "Sprache:",
        "record_key":  "[Taste drücken]",
        "cancel_key":  "[abgebrochen]",
        "reload":      "↻",
        "show":        "show",
        "hide":        "hide",
        "tray_toggle": "Anzeigen / Verstecken",
        "tray_quit":   "Beenden",
    },
    "en": {
        "title":       "IP Calculator",
        "network":     "Network",
        "broadcast":   "Broadcast",
        "mask":        "Subnet Mask",
        "first":       "First Host",
        "last":        "Last Host",
        "hosts":       "Hosts",
        "invalid_ip":  "Invalid IP address",
        "invalid_cidr":"CIDR must be 0–32",
        "settings":    "Settings",
        "hotkey":      "Hotkey",
        "key":         "Key:",
        "record":      "record",
        "transparency":"Transparency",
        "ghost":       "ghost %:",
        "solid":       "solid %:",
        "window":      "Window",
        "topmost":     "Always on top:",
        "apply":       "Apply",
        "cancel":      "Cancel",
        "language":    "Language:",
        "record_key":  "[Press key]",
        "cancel_key":  "[cancelled]",
        "reload":      "↻",
        "show":        "show",
        "hide":        "hide",
        "tray_toggle": "Show / Hide",
        "tray_quit":   "Quit",
    }
}

def t(key):
    return STRINGS.get(LANG, STRINGS["de"]).get(key, key)

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

def _make_tray_image():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    d.rounded_rectangle([2, 2, 62, 62], radius=14, fill="#112211")
    d.rounded_rectangle([2, 2, 62, 62], radius=14, outline="#2a5a3a", width=2)
    try:
        font = ImageFont.truetype("consola.ttf", 26)
    except Exception:
        font = ImageFont.load_default()
    d.text((8, 16), "IP", fill="#8fce9f", font=font)
    try:
        small = ImageFont.truetype("consola.ttf", 11)
    except Exception:
        small = ImageFont.load_default()
    d.text((9, 44), "/24", fill="#4a7a5a", font=small)
    return img

class IPRechner:

    def __init__(self):
        self.alpha_ghost             = 0.12
        self.alpha_solid             = 0.85
        self.current_alpha           = 0.85
        self.hidden                  = False
        self.minimized               = False
        self.topmost                 = True
        self.hotkey_key              = "x"
        self.recording               = False
        self._drag                   = {}
        self._hotkey_thread_running  = False
        self._hotkey_thread          = None
        self._tray_icon              = None
        self._pynput_listener        = None
        self._ctrl_state             = False

        self._load_config()
        self._build_window()
        self._build_ui()
        self._bind_local()
        self._start_global_hotkey()
        if PYSTRAY_AVAILABLE:
            self._start_tray_icon()
        self._calculate()
        self.root.mainloop()

    def _load_config(self):
        global LANG
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    cfg = json.load(f)
                    LANG              = cfg.get("language",    "de")
                    self.hotkey_key   = cfg.get("hotkey_key",  "x")
                    self.alpha_ghost  = cfg.get("alpha_ghost", 0.12)
                    self.alpha_solid  = cfg.get("alpha_solid", 0.85)
                    self.topmost      = cfg.get("topmost",     True)
        except Exception:
            pass

    def _save_config(self):
        try:
            cfg = {
                "language":    LANG,
                "hotkey_key":  self.hotkey_key,
                "alpha_ghost": self.alpha_ghost,
                "alpha_solid": self.alpha_solid,
                "topmost":     self.topmost,
            }
            with open(CONFIG_FILE, "w") as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass

    def _build_window(self):
        self.root = ctk.CTk()
        self.root.title(t("title"))
        self.root.geometry(f"{W}x{H}")
        self.root.resizable(False, False)
        self.root.overrideredirect(True)
        self.root.attributes("-alpha",   self.current_alpha)
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
        self._bar = ctk.CTkFrame(self.root, fg_color=BG, height=20)
        self._bar.pack(fill="x")
        self._bar.pack_propagate(False)

        self._title_label = ctk.CTkLabel(
            self._bar, text=f"  {t('title')}",
            font=("Consolas", 7), text_color="#6a9a7a", anchor="w"
        )
        self._title_label.pack(side="left", fill="y")

        ctk.CTkButton(
            self._bar, text="×", width=20, height=18,
            fg_color="transparent", hover_color="#2a2a2a",
            text_color="#8a9a8a", font=("Consolas", 11),
            command=self._quit
        ).pack(side="right", padx=(0, 1))

        ctk.CTkButton(
            self._bar, text="–", width=20, height=18,
            fg_color="transparent", hover_color="#1a1a1a",
            text_color="#7a8a7a", font=("Consolas", 11),
            command=self._toggle_minimize
        ).pack(side="right")

        ctk.CTkButton(
            self._bar, text="⚙", width=20, height=18,
            fg_color="transparent", hover_color="#1a1a1a",
            text_color="#6a8a7a", font=("Consolas", 10),
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
        frame.pack(fill="x", padx=6, pady=(4, 2))

        self.entry_ip = ctk.CTkEntry(
            frame, width=110, height=22, font=("Consolas", 10),
            fg_color="#1a2a1a", text_color="#7aaa9a",
            border_color="#2a3a2a", border_width=1,
            placeholder_text="192.168.1.0"
        )
        self.entry_ip.pack(side="left")
        self.entry_ip.insert(0, "192.168.1.0")
        self.entry_ip.bind("<Return>", self._calculate)

        ctk.CTkLabel(
            frame, text=" / ", font=("Consolas", 10),
            text_color="#1a2a1a"
        ).pack(side="left", padx=2)

        self.entry_cidr = ctk.CTkEntry(
            frame, width=28, height=22, font=("Consolas", 10),
            fg_color="#1a2a1a", text_color="#7aaa9a",
            border_color="#2a3a2a", border_width=1,
            placeholder_text="24"
        )
        self.entry_cidr.pack(side="left")
        self.entry_cidr.insert(0, "24")
        self.entry_cidr.bind("<Return>", self._calculate)

        ctk.CTkButton(
            frame, text=t("reload"), width=22, height=22,
            font=("Consolas", 8),
            fg_color="#1a2a1a", hover_color="#2a4a3a",
            text_color="#6a9a8a", command=self._calculate
        ).pack(side="left", padx=(3, 0))

    def _build_results(self):
        ROWS = [
            (t("network"),   "net"),
            (t("broadcast"), "bc"),
            (t("mask"),      "mask"),
            (t("first"),     "first"),
            (t("last"),      "last"),
            (t("hosts"),     "hosts"),
        ]
        self.val_labels = {}
        for title, key in ROWS:
            row = ctk.CTkFrame(self._content, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=0)
            ctk.CTkLabel(
                row, text=title, font=("Consolas", 8),
                text_color=FG_LABEL, anchor="w", width=70
            ).pack(side="left")
            lbl = ctk.CTkLabel(
                row, text="", font=("Consolas", 9),
                text_color=FG_VAL, anchor="w"
            )
            lbl.pack(side="left")
            self.val_labels[key] = lbl

    def _build_bottom_bar(self):
        bar = ctk.CTkFrame(self._content, fg_color="transparent")
        bar.pack(fill="x", padx=6, pady=(2, 3))

        self.btn_hide = ctk.CTkButton(
            bar, text=t("hide"), width=36, height=18,
            font=("Consolas", 8),
            fg_color="#1a2a1a", hover_color="#2a4a3a",
            text_color="#7aaa9a", command=self.toggle_visibility
        )
        self.btn_hide.pack(side="left", padx=(0, 3))

        ctk.CTkButton(
            bar, text="ghost", width=38, height=18,
            font=("Consolas", 8),
            fg_color="#1a2a1a", hover_color="#2a4a3a",
            text_color="#6a9a8a",
            command=lambda: self._set_alpha(self.alpha_ghost)
        ).pack(side="left", padx=(0, 2))

        ctk.CTkButton(
            bar, text="solid", width=38, height=18,
            font=("Consolas", 8),
            fg_color="#1a2a1a", hover_color="#2a4a3a",
            text_color="#7aaa9a",
            command=lambda: self._set_alpha(self.alpha_solid)
        ).pack(side="left")

    def _sep(self):
        ctk.CTkFrame(self._content, height=1, fg_color="#0d0d0d").pack(
            fill="x", padx=6, pady=1
        )

    def _calculate(self, *_):
        raw_ip  = self.entry_ip.get().strip()
        raw_cdr = self.entry_cidr.get().strip()

        def err(msg):
            for lbl in self.val_labels.values():
                lbl.configure(text="", text_color=FG_VAL)
            self.val_labels["net"].configure(text=msg, text_color=FG_ERR)

        if not validate_ip(raw_ip):
            err(t("invalid_ip"))
            return
        try:
            c = int(raw_cdr)
            assert 0 <= c <= 32
        except (ValueError, AssertionError):
            err(t("invalid_cidr"))
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

        self.val_labels["net"].configure(  text=int_to_ip(net),   text_color=FG_VAL)
        self.val_labels["bc"].configure(   text=int_to_ip(bc),    text_color=FG_VAL)
        self.val_labels["mask"].configure( text=f"{int_to_ip(mask)}  (/{c})", text_color=FG_VAL)
        self.val_labels["first"].configure(text=int_to_ip(first), text_color=FG_VAL)
        self.val_labels["last"].configure( text=int_to_ip(last),  text_color=FG_VAL)
        self.val_labels["hosts"].configure(
            text=f"{hosts:,}".replace(",", ".") + f" {t('hosts')}",
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
            self.btn_hide.configure(text=t("show"))
        else:
            self.root.attributes("-alpha", self.current_alpha)
            self.btn_hide.configure(text=t("hide"))

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

    def _start_global_hotkey(self):
        self._stop_global_hotkey()
        self._hotkey_thread_running = True

        if sys.platform == "win32":
            def _win_thread():
                user32 = ctypes.windll.user32
                user32.UnregisterHotKey(None, _HOTKEY_ID)
                vk = user32.VkKeyScanW(ctypes.c_wchar(self.hotkey_key[0])) & 0xFF
                ok = user32.RegisterHotKey(None, _HOTKEY_ID, MOD_CONTROL, vk)
                if not ok:
                    self._start_pynput_hotkey()
                    return
                msg = ctypes.wintypes.MSG()
                while self._hotkey_thread_running:
                    if user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                        if msg.message == WM_HOTKEY and msg.wParam == _HOTKEY_ID:
                            self.root.after(0, self.toggle_visibility)
                    else:
                        time.sleep(0.04)
                user32.UnregisterHotKey(None, _HOTKEY_ID)

            self._hotkey_thread = threading.Thread(target=_win_thread, daemon=True)
            self._hotkey_thread.start()
        else:
            self._start_pynput_hotkey()

    def _stop_global_hotkey(self):
        self._hotkey_thread_running = False
        if self._pynput_listener is not None:
            try:
                self._pynput_listener.stop()
            except Exception:
                pass
            self._pynput_listener = None

    def _start_pynput_hotkey(self):
        if not PYNPUT_AVAILABLE:
            return
        self._ctrl_state = False

        def on_press(key):
            if not self._hotkey_thread_running or self.recording:
                return
            try:
                if key in (_kb.Key.ctrl_l, _kb.Key.ctrl_r):
                    self._ctrl_state = True
                    return
                if self._ctrl_state:
                    char = None
                    try:
                        char = key.char.lower() if hasattr(key, "char") and key.char else None
                    except Exception:
                        pass
                    if char and char == self.hotkey_key.lower():
                        self.root.after(0, self.toggle_visibility)
            except Exception:
                pass

        def on_release(key):
            try:
                if key in (_kb.Key.ctrl_l, _kb.Key.ctrl_r):
                    self._ctrl_state = False
            except Exception:
                pass

        self._pynput_listener = _kb.Listener(on_press=on_press, on_release=on_release)
        self._pynput_listener.start()

    def _start_tray_icon(self):
        if not PYSTRAY_AVAILABLE:
            return

        menu = pystray.Menu(
            pystray.MenuItem(
                t("tray_toggle"),
                lambda icon, item: self.root.after(0, self.toggle_visibility),
                default=True
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                t("tray_quit"),
                lambda icon, item: self.root.after(0, self._quit)
            ),
        )

        self._tray_icon = pystray.Icon(
            "ip_rechner",
            _make_tray_image(),
            f"IP-Rechner {VERSION}",
            menu=menu
        )
        self._tray_icon.run_detached()

    def _stop_tray_icon(self):
        if self._tray_icon is not None:
            try:
                self._tray_icon.stop()
            except Exception:
                pass
            self._tray_icon = None

    def _bind_local(self):
        self.entry_ip.bind("<Return>",   self._calculate)
        self.entry_cidr.bind("<Return>", self._calculate)
        self.root.bind("<Escape>",       lambda e: self._quit())
        self._bind_local_hotkey()

    def _bind_local_hotkey(self):
        for seq in (f"<Control-{self.hotkey_key}>", f"<Control-{self.hotkey_key.upper()}>"):
            try:
                self.root.bind(seq, self.toggle_visibility)
            except Exception:
                pass

    def _quit(self):
        self._stop_global_hotkey()
        self._stop_tray_icon()
        self._save_config()
        try:
            self.root.destroy()
        except Exception:
            pass

    def _open_settings(self):
        if hasattr(self, "_settings_win") and self._settings_win.winfo_exists():
            self._settings_win.focus()
            return

        win = ctk.CTkToplevel(self.root)
        win.title(t("settings"))
        win.geometry("290x460")
        win.resizable(False, False)
        win.attributes("-topmost", True)
        win.configure(fg_color="#0a0a0a")
        win.grab_set()
        self._settings_win = win

        ctk.CTkLabel(
            win, text=f"IP-Rechner {VERSION}",
            font=("Consolas", 11, "bold"), text_color=FG_VAL
        ).pack(pady=(8, 3))

        def section(text):
            ctk.CTkLabel(
                win, text=text, font=("Consolas", 8, "bold"),
                text_color=FG_LABEL
            ).pack(anchor="w", padx=10, pady=(8, 1))

        def card():
            f = ctk.CTkFrame(win, fg_color=FG_SUBTLE, corner_radius=4)
            f.pack(fill="x", padx=8, pady=(0, 1))
            return f

        def row(parent):
            r = ctk.CTkFrame(parent, fg_color="transparent")
            r.pack(fill="x", padx=6, pady=2)
            return r

        section(t("language"))
        f_lang = card()
        r_lang = row(f_lang)
        ctk.CTkLabel(r_lang, text=t("language"), font=("Consolas", 8),
                     text_color=FG_LABEL, width=60, anchor="w").pack(side="left")
        self._lang_var = ctk.StringVar(value="Deutsch" if LANG == "de" else "English")
        ctk.CTkComboBox(
            r_lang, values=["Deutsch", "English"],
            variable=self._lang_var, width=80, height=22,
            font=("Consolas", 9),
            fg_color="#0f0f0f", text_color="#4a8d6a",
            border_color="#0f0f0f", button_color="#0f0f0f"
        ).pack(side="left")

        section(t("hotkey"))
        f_hk = card()
        r1 = row(f_hk)
        ctk.CTkLabel(r1, text=t("key"), font=("Consolas", 8),
                     text_color=FG_LABEL, width=60, anchor="w").pack(side="left")
        self._lbl_key = ctk.CTkLabel(
            r1, text=f"Ctrl+{self.hotkey_key.upper()}",
            font=("Consolas", 9), text_color=FG_VAL, width=50, anchor="w"
        )
        self._lbl_key.pack(side="left")
        ctk.CTkButton(
            r1, text=t("record"), width=60, height=20,
            font=("Consolas", 8),
            fg_color="#0f0f0f", hover_color="#1a1a1a",
            text_color=FG_LABEL, command=lambda: self._start_record(win)
        ).pack(side="right", padx=(2, 0))

        if sys.platform == "win32":
            ctk.CTkLabel(
                win, text="  ✓ globaler Hotkey via Windows-API",
                font=("Consolas", 7), text_color=FG_LABEL
            ).pack(anchor="w", padx=10, pady=(0, 1))
        elif not PYNPUT_AVAILABLE:
            ctk.CTkLabel(
                win, text="  ⚠ pynput fehlt – nur bei Fokus aktiv",
                font=("Consolas", 7), text_color=FG_ACT
            ).pack(anchor="w", padx=10, pady=(0, 1))

        section(t("transparency"))
        f_tr = card()

        r_g = row(f_tr)
        ctk.CTkLabel(r_g, text=t("ghost"), font=("Consolas", 8),
                     text_color=FG_LABEL, width=60, anchor="w").pack(side="left")
        self._entry_ghost = ctk.CTkEntry(
            r_g, width=40, height=20, font=("Consolas", 9),
            fg_color="#0f0f0f", text_color="#4a8d6a",
            border_color="#0f0f0f", border_width=0
        )
        self._entry_ghost.insert(0, str(int(self.alpha_ghost * 100)))
        self._entry_ghost.pack(side="left")
        ctk.CTkLabel(r_g, text="%", font=("Consolas", 8),
                     text_color=FG_LABEL).pack(side="left", padx=(2, 0))

        r_s = row(f_tr)
        ctk.CTkLabel(r_s, text=t("solid"), font=("Consolas", 8),
                     text_color=FG_LABEL, width=60, anchor="w").pack(side="left")
        self._entry_solid = ctk.CTkEntry(
            r_s, width=40, height=20, font=("Consolas", 9),
            fg_color="#0f0f0f", text_color="#4a8d6a",
            border_color="#0f0f0f", border_width=0
        )
        self._entry_solid.insert(0, str(int(self.alpha_solid * 100)))
        self._entry_solid.pack(side="left")
        ctk.CTkLabel(r_s, text="%", font=("Consolas", 8),
                     text_color=FG_LABEL).pack(side="left", padx=(2, 0))

        section(t("window"))
        f_win = card()
        r_top = row(f_win)
        ctk.CTkLabel(r_top, text=t("topmost"), font=("Consolas", 8),
                     text_color=FG_LABEL, width=80, anchor="w").pack(side="left")
        self._topmost_var = ctk.BooleanVar(value=self.topmost)
        ctk.CTkSwitch(
            r_top, variable=self._topmost_var, text="",
            width=36, height=16,
            fg_color="#0f0f0f", progress_color="#1a3a2a",
            button_color="#2a5a4a", button_hover_color="#3a7a6a"
        ).pack(side="left")

        if not PYSTRAY_AVAILABLE:
            ctk.CTkLabel(
                win, text="  ⚠ pystray/pillow fehlt – kein Tray-Icon\n  pip install pystray pillow",
                font=("Consolas", 7), text_color=FG_ACT, justify="left"
            ).pack(anchor="w", padx=10, pady=(4, 0))

        frame_btn = ctk.CTkFrame(win, fg_color="transparent")
        frame_btn.pack(fill="x", padx=8, pady=(8, 6))

        ctk.CTkButton(
            frame_btn, text=t("apply"), width=90, height=22,
            font=("Consolas", 8),
            fg_color="#0f0f0f", hover_color="#1a1a1a",
            text_color=FG_VAL,
            command=lambda: self._apply_settings(win)
        ).pack(side="right", padx=(2, 0))

        ctk.CTkButton(
            frame_btn, text=t("cancel"), width=80, height=22,
            font=("Consolas", 8),
            fg_color="#0f0f0f", hover_color="#1a1a1a",
            text_color=FG_LABEL, command=win.destroy
        ).pack(side="right")

    def _apply_settings(self, win):
        global LANG
        lang_map      = {"Deutsch": "de", "English": "en"}
        new_lang      = lang_map.get(self._lang_var.get(), "de")
        lang_changed  = (new_lang != LANG)
        LANG          = new_lang

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
        self._save_config()
        self._bind_local_hotkey()
        self._start_global_hotkey()
        win.destroy()

        if lang_changed:
            self._update_ui_language()

    def _start_record(self, parent_win):
        self.recording = True
        self._lbl_key.configure(text=t("record_key"), text_color=FG_ACT)
        parent_win.bind("<KeyPress>", lambda e: self._on_key_record(e, parent_win))
        parent_win.focus_set()

    def _on_key_record(self, e, parent_win):
        IGNORE = {
            "Shift_L", "Shift_R", "Control_L", "Control_R",
            "Alt_L",   "Alt_R",   "Super_L",   "Super_R",
            "Escape",  "Return",  "Tab"
        }
        if e.keysym in IGNORE:
            self._lbl_key.configure(text=t("cancel_key"), text_color=FG_ERR)
            self.root.after(1200, lambda: self._lbl_key.configure(
                text=f"Ctrl+{self.hotkey_key.upper()}", text_color=FG_VAL))
        else:
            self.hotkey_key = e.keysym.lower()
            self._lbl_key.configure(text=f"Ctrl+{self.hotkey_key.upper()}", text_color=FG_VAL)
        self.recording = False
        parent_win.unbind("<KeyPress>")

    def _update_ui_language(self):
        self._title_label.configure(text=f"  {t('title')}")
        for widget in self._content.winfo_children():
            widget.destroy()
        self._build_inputs()
        self._sep()
        self._build_results()
        self._sep()
        self._build_bottom_bar()
        self._calculate()


if __name__ == "__main__":
    IPRechner()
