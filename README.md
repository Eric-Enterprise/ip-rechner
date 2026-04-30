# 🧮 IP-Rechner

> Minimalistisches Subnetz-Tool für den Desktop — immer im Vordergrund, immer bereit.

![Python](https://img.shields.io/badge/Python-3.8+-3a6040?style=flat-square&logo=python&logoColor=white)
![GUI](https://img.shields.io/badge/GUI-customtkinter-1e3025?style=flat-square)
![Hotkey](https://img.shields.io/badge/Hotkey-WinAPI%20%7C%20pynput-1e3025?style=flat-square)
![Tray](https://img.shields.io/badge/Tray-pystray-1e3025?style=flat-square)
![License](https://img.shields.io/badge/Lizenz-MIT-4a6050?style=flat-square)

---

## Vorschau

```
┌─────────────────────────────────────┐
│  IP-Rechner              ⚙  –  ×   │
├─────────────────────────────────────┤
│  192.168.1.0        /  24     [↻]   │
├─────────────────────────────────────┤
│  Netzadresse    192.168.1.0         │
│  Broadcast      192.168.1.255       │
│  Subnetzmaske   255.255.255.0 (/24) │
│  Erster Host    192.168.1.1         │
│  Letzter Host   192.168.1.254       │
│  Hosts          254 Hosts           │
├─────────────────────────────────────┤
│  [hide]   [ghost]   [solid]         │
└─────────────────────────────────────┘
```

---

## Features

| Feature | Beschreibung |
|---|---|
| **CIDR-Kalkulation** | Netzadresse, Broadcast, Maske, erster/letzter Host und Hostanzahl |
| **Always-on-Top** | Schwebt über jeder Anwendung, chromlos via `overrideredirect` |
| **Transparenzmodi** | `ghost` & `solid`, frei konfigurierbar |
| **Globaler Hotkey** | `Ctrl + Taste`, systemweit (WinAPI / pynput Fallback) |
| **Persistente Settings** | Einstellungen werden automatisch gespeichert |
| **Mehrsprachig** | Deutsch / Englisch umschaltbar |
| **System Tray** | Minimieren in Tray + Steuerung im Hintergrund |
| **Freie Positionierung** | Fenster per Drag bewegbar |
| **Einstellungen** | Hotkey, Transparenz, Sprache, Always-on-Top |
| **Minimieren** | Auf Titelleiste (24 px) reduzieren |

---

## Installation

### 1. Abhängigkeiten installieren

```bash
# Pflicht
pip install customtkinter

# Optional (empfohlen)
pip install pynput pystray pillow
```

### 2. Starten

```bash
python ip_rechner.py
```

### Linux / macOS — direkt ausführbar

```bash
chmod +x ip_rechner.py
./ip_rechner.py
```

---

## Abhängigkeiten

| Paket | Zweck | Status |
|---|---|---|
| `customtkinter` | Modernes Tkinter-Theme (Dark Mode, Blue Theme) | **Pflicht** |
| `pynput` | Globale Hotkeys (macOS/Linux) | Optional |
| `pystray` | System Tray Integration | Optional |
| `pillow` | Tray-Icon Rendering | Optional |
| `struct`, `socket` | IP-Arithmetik | Stdlib |

> **Hinweise:**  
> - Unter Windows werden Hotkeys nativ über die WinAPI umgesetzt  
> - Ohne `pynput` funktioniert der Hotkey nur im Fokus (macOS/Linux)  
> - Ohne `pystray` wird kein Tray-Icon angezeigt  

---

## Bedienung

### Berechnung

1. IP-Adresse eingeben (z. B. `10.0.0.0`)
2. CIDR-Präfix eingeben (z. B. `16`)
3. `↻` klicken **oder** `Enter` drücken  

---

### Tastenkürzel

| Taste | Aktion |
|---|---|
| `Ctrl + X` *(Standard)* | Fenster global ein-/ausblenden |
| `Enter` | Berechnung auslösen |
| `Escape` | Programm beenden |
| `–` | Minimieren |
| `⚙` | Einstellungen öffnen |

---

### Transparenz

- **ghost** — fast unsichtbar (Standard: 12 %)  
- **solid** — hohe Sichtbarkeit (Standard: 85 %)  
- **hide / show** — komplett ausblenden (Alpha = 0)  

---

## Einstellungen

Über die `⚙`-Schaltfläche erreichbar:

- **Sprache** — Deutsch / Englisch  
- **Hotkey** — frei belegbar („aufnehmen")  
- **ghost %** — Transparenz (1–99)  
- **solid %** — Transparenz (1–100)  
- **Immer vorne** — Always-on-Top  

> Alle Einstellungen werden automatisch gespeichert (`~/.ip_rechner_config.json`)

---

## Berechnungslogik

```
Subnetzmaske  = 0xFFFFFFFF << (32 − CIDR)  &  0xFFFFFFFF
Netzadresse   = IP  &  Maske
Broadcast     = Netz  |  ~Maske

Erster Host   = Netz + 1        (für /0 – /30)
Letzter Host  = Broadcast − 1  (für /0 – /30)

/31  →  2 Hosts  (RFC 3021)
/32  →  1 Host
```

---

## Projektstruktur

```
ip_rechner.py      # Gesamte Anwendung
README.md          # Diese Datei
```

---

## Voraussetzungen

- Python **3.8+**
- Tkinter
- Windows, macOS oder Linux

---

## Lizenz

MIT — freie Nutzung, Weitergabe und Modifikation erlaubt.
